from abc import ABC, abstractmethod
from typing import List, Optional, Union
import asyncio
from ..results import MeasurementResult
from ..exceptions import InstrumentError, InstrumentTimeout, ConnectionLost, OverloadError, ConfigurationError

class InstrumentDriver(ABC):
    """Abstract Base Class for all instrument drivers."""
    def __init__(self, resource: str):
        self.resource = resource
        self.connected = False

    @property
    def resource_address(self) -> str:
        """Alias for self.resource for backward compatibility."""
        return self.resource

    @abstractmethod
    def connect(self):
        """Establishes a connection to the instrument."""
        pass

    @abstractmethod
    def disconnect(self):
        """Closes the connection to the instrument."""
        pass

    def close(self):
        """Alias for disconnect()."""
        self.disconnect()

    def write(self, command: str):
        """Sends a SCPI command to the instrument."""
        raise NotImplementedError(f"write() not implemented in {self.__class__.__name__}")

    def query(self, command: str) -> str:
        """Sends a SCPI command and returns the response."""
        raise NotImplementedError(f"query() not implemented in {self.__class__.__name__}")

    @abstractmethod
    def get_id(self) -> str:
        """Returns the identification string of the instrument."""
        pass

    # Basic measurements available on most instruments
    @abstractmethod
    def measure_frequency(self) -> MeasurementResult:
        """Measures frequency."""
        pass

    @abstractmethod
    def measure_duty_cycle(self) -> MeasurementResult:
        """Measures duty cycle."""
        pass

    @abstractmethod
    def measure_v_peak_to_peak(self) -> MeasurementResult:
        """Measures peak-to-peak voltage."""
        pass

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def __getattr__(self, name: str):
        """Dynamic async wrapper for any method starting with 'async_'."""
        if name.startswith("async_"):
            real_method_name = name[6:]
            if hasattr(self, real_method_name):
                method = getattr(self, real_method_name)
                if callable(method):
                    return lambda *args, **kwargs: asyncio.to_thread(method, *args, **kwargs)
        
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

class Multimeter(InstrumentDriver):
    """Interface for Digital Multimeters (DMM)."""
    @abstractmethod
    def measure_voltage(self) -> MeasurementResult:
        """Measures DC Voltage."""
        pass

    @abstractmethod
    def measure_resistance(self) -> MeasurementResult:
        """Measures Resistance."""
        pass

class PowerSupply(InstrumentDriver):
    """Interface for Programmable Power Supplies (PSU)."""
    @abstractmethod
    def set_voltage(self, voltage: float):
        """Sets the output voltage level."""
        pass

    @abstractmethod
    def get_voltage(self) -> float:
        """Reads the currently set output voltage."""
        pass

    @abstractmethod
    def set_current_limit(self, current: float):
        """Sets the output current limit."""
        pass

    @abstractmethod
    def get_current(self) -> MeasurementResult:
        """Measures the actual output current."""
        pass

    @abstractmethod
    def set_output(self, state: bool):
        """Enables or disables the output."""
        pass

    @abstractmethod
    def get_output(self) -> bool:
        """Checks if the output is enabled."""
        pass

class SpectrumAnalyzer(InstrumentDriver):
    """Interface for Spectrum Analyzers (SA)."""
    @abstractmethod
    def peak_search(self):
        """Moves a marker to the highest peak."""
        pass

    @abstractmethod
    def get_marker_amplitude(self) -> MeasurementResult:
        """Returns the amplitude at the current marker."""
        pass

    def get_peak_value(self) -> MeasurementResult:
        """Combined Peak Search + Amplitude measurement."""
        self.peak_search()
        return self.get_marker_amplitude()

class NetworkAnalyzer(InstrumentDriver):
    """Interface for Vector Network Analyzers (VNA)."""
    @abstractmethod
    def set_start_frequency(self, freq_hz: float):
        """Sets the sweep start frequency."""
        pass

    @abstractmethod
    def set_stop_frequency(self, freq_hz: float):
        """Sets the sweep stop frequency."""
        pass

    @abstractmethod
    def set_points(self, num_points: int):
        """Sets the number of data points."""
        pass

    @abstractmethod
    def get_trace_data(self, measurement_name: str) -> MeasurementResult:
        """Acquires formatted trace data."""
        pass

    @abstractmethod
    def get_complex_trace(self, measurement_name: str) -> MeasurementResult:
        """Acquires complex (I/Q) trace data."""
        pass

class Oscilloscope(InstrumentDriver):
    """Interface for Digital Storage Oscilloscopes (DSO)."""
    @abstractmethod
    def run(self):
        """Starts acquisition."""
        pass

    @abstractmethod
    def stop(self):
        """Stops acquisition."""
        pass

    @abstractmethod
    def single(self):
        """Triggers a single acquisition."""
        pass

    @abstractmethod
    def get_waveform(self, channel: int) -> MeasurementResult:
        """Acquires the time-domain waveform."""
        pass

class MixedSignalOscilloscope(Oscilloscope):
    """Interface for Oscilloscopes with digital logic channels."""
    @abstractmethod
    def get_digital_waveform(self, pod: int) -> MeasurementResult:
        """Acquires digital logic data."""
        pass

class SignalGenerator(InstrumentDriver):
    """Interface for RF Signal Generators (SG)."""
    @abstractmethod
    def set_frequency(self, hz: float):
        """Sets the output carrier frequency."""
        pass

    @abstractmethod
    def set_amplitude(self, dbm: float):
        """Sets the output amplitude level."""
        pass

    @abstractmethod
    def set_output(self, state: bool):
        """Enables or disables the RF output."""
        pass
