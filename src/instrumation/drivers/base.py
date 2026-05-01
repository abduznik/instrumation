from abc import ABC, abstractmethod
import asyncio
from ..results import MeasurementResult

class InstrumentDriver(ABC):
    """Abstract Base Class for Generic Instruments.

    Attributes:
        resource: The underlying resource object or connection string.
        connected (bool): Connection status of the instrument.
    """
    def __init__(self, resource):
        """Initializes the InstrumentDriver.

        Args:
            resource: The resource to connect to.
        """
        self.resource = resource
        self.connected = False

    def __enter__(self):
        """Connects to the instrument when entering the context."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Disconnects from the instrument when exiting the context."""
        self.disconnect()

    @abstractmethod
    def connect(self):
        """Establishes connection to the instrument."""
        pass

    @abstractmethod
    def disconnect(self):
        """Closes the connection to the instrument."""
        pass

    @abstractmethod
    def get_id(self) -> str:
        """Returns the identification string of the instrument.

        Returns:
            str: The identification string.
        """
        pass

    @abstractmethod
    def measure_frequency(self) -> MeasurementResult:
        """Measures the frequency of the input signal.

        Returns:
            MeasurementResult: The measured frequency.
        """
        pass

    @abstractmethod
    def measure_duty_cycle(self) -> MeasurementResult:
        """Measures the duty cycle of the input signal as a percentage.

        Returns:
            MeasurementResult: The duty cycle.
        """
        pass

    @abstractmethod
    def measure_v_peak_to_peak(self) -> MeasurementResult:
        """Measures the peak-to-peak voltage of the input signal.

        Returns:
            MeasurementResult: The peak-to-peak voltage.
        """
        pass

    # --- Async Support ---

    async def async_measure_frequency(self) -> MeasurementResult:
        """Asynchronously measures the frequency."""
        return await asyncio.to_thread(self.measure_frequency)

    async def async_measure_duty_cycle(self) -> MeasurementResult:
        """Asynchronously measures the duty cycle."""
        return await asyncio.to_thread(self.measure_duty_cycle)

    async def async_measure_v_peak_to_peak(self) -> MeasurementResult:
        """Asynchronously measures the peak-to-peak voltage."""
        return await asyncio.to_thread(self.measure_v_peak_to_peak)

class Multimeter(InstrumentDriver):
    """Abstract Base Class for Digital Multimeters."""
    @abstractmethod
    def measure_voltage(self) -> MeasurementResult:
        """Measures the DC voltage.

        Returns:
            MeasurementResult: The measured voltage.
        """
        pass
    
    @abstractmethod
    def measure_resistance(self) -> MeasurementResult:
        """Measures the resistance.

        Returns:
            MeasurementResult: The measured resistance.
        """
        pass

    async def async_measure_voltage(self) -> MeasurementResult:
        """Asynchronously measures the DC voltage."""
        return await asyncio.to_thread(self.measure_voltage)

    async def async_measure_resistance(self) -> MeasurementResult:
        """Asynchronously measures the resistance."""
        return await asyncio.to_thread(self.measure_resistance)

class PowerSupply(InstrumentDriver):
    """Abstract Base Class for DC Power Supplies."""
    @abstractmethod
    def set_voltage(self, voltage: float):
        """Sets the output voltage.

        Args:
            voltage (float): The voltage level to set in Volts.
        """
        pass
    
    @abstractmethod
    def get_current(self) -> MeasurementResult:
        """Reads the current output current.

        Returns:
            MeasurementResult: The measured current.
        """
        pass

    async def async_get_current(self) -> MeasurementResult:
        """Asynchronously reads the current output current."""
        return await asyncio.to_thread(self.get_current)

class SpectrumAnalyzer(InstrumentDriver):
    """Abstract Base Class for Spectrum Analyzers."""
    @abstractmethod
    def peak_search(self):
        """Moves marker to the highest peak."""
        pass

    @abstractmethod
    def get_marker_amplitude(self) -> MeasurementResult:
        """Returns the amplitude at the current marker.

        Returns:
            MeasurementResult: The amplitude value.
        """
        pass

    async def async_get_marker_amplitude(self) -> MeasurementResult:
        """Asynchronously returns the amplitude at the current marker."""
        return await asyncio.to_thread(self.get_marker_amplitude)

    async def async_get_peak_value(self) -> MeasurementResult:
        """Asynchronously performs peak search and returns amplitude."""
        # Note: We can't use to_thread for the whole thing easily if we want to yield
        # but for simple wrapping it works.
        return await asyncio.to_thread(self.get_peak_value)

    def get_peak_value(self) -> MeasurementResult:
        """Helper: Performs peak search and returns amplitude.

        Returns:
            MeasurementResult: The peak amplitude value.
        """
        self.peak_search()
        return self.get_marker_amplitude()

class NetworkAnalyzer(InstrumentDriver):
    """Abstract Base Class for Vector Network Analyzers."""
    @abstractmethod
    def set_start_frequency(self, freq_hz: float):
        """Sets the start frequency for the sweep.

        Args:
            freq_hz (float): The start frequency in Hz.
        """
        pass

    @abstractmethod
    def set_stop_frequency(self, freq_hz: float):
        """Sets the stop frequency for the sweep.

        Args:
            freq_hz (float): The stop frequency in Hz.
        """
        pass

    @abstractmethod
    def set_points(self, num_points: int):
        """Sets the number of points for the sweep.

        Args:
            num_points (int): The number of measurement points.
        """
        pass

    @abstractmethod
    def get_trace_data(self, measurement_name: str) -> MeasurementResult:
        """Returns the formatted data trace.

        Args:
            measurement_name (str): The name of the measurement/trace to retrieve.

        Returns:
            MeasurementResult: The trace data points (as a list).
        """
        pass

    async def async_get_trace_data(self, measurement_name: str) -> MeasurementResult:
        """Asynchronously returns the formatted data trace."""
        return await asyncio.to_thread(self.get_trace_data, measurement_name)

class Oscilloscope(InstrumentDriver):
    """Abstract Base Class for Oscilloscopes."""
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
        """Sets the oscilloscope to single acquisition mode."""
        pass

    @abstractmethod
    def get_waveform(self, channel: int) -> MeasurementResult:
        """Returns the waveform data for the specified channel.

        Args:
            channel (int): The channel number to read from.

        Returns:
            MeasurementResult: The waveform data points (as a list).
        """
        pass

    async def async_get_waveform(self, channel: int) -> MeasurementResult:
        """Asynchronously returns the waveform data for the specified channel."""
        return await asyncio.to_thread(self.get_waveform, channel)

class SignalGenerator(InstrumentDriver):
    """Abstract Base Class for Signal Generators."""
    @abstractmethod
    def set_frequency(self, hz: float):
        """Sets the output frequency.

        Args:
            hz (float): The frequency level to set in Hz.
        """
        pass

    @abstractmethod
    def set_amplitude(self, dbm: float):
        """Sets the output amplitude.

        Args:
            dbm (float): The amplitude level to set in dBm.
        """
        pass

    @abstractmethod
    def set_output(self, state: bool):
        """Enables or disables the signal output.

        Args:
            state (bool): True to enable, False to disable.
        """
        pass
