from abc import ABC, abstractmethod

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
    def measure_frequency(self) -> float:
        """Measures the frequency of the input signal.

        Returns:
            float: The measured frequency in Hz.
        """
        pass

    @abstractmethod
    def measure_duty_cycle(self) -> float:
        """Measures the duty cycle of the input signal as a percentage.

        Returns:
            float: The duty cycle in percent (0-100).
        """
        pass

    @abstractmethod
    def measure_v_peak_to_peak(self) -> float:
        """Measures the peak-to-peak voltage of the input signal.

        Returns:
            float: The peak-to-peak voltage in Volts.
        """
        pass

class Multimeter(InstrumentDriver):
    """Abstract Base Class for Digital Multimeters."""
    @abstractmethod
    def measure_voltage(self) -> float:
        """Measures the DC voltage.

        Returns:
            float: The measured voltage in Volts.
        """
        pass
    
    @abstractmethod
    def measure_resistance(self) -> float:
        """Measures the resistance.

        Returns:
            float: The measured resistance in Ohms.
        """
        pass

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
    def get_current(self) -> float:
        """Reads the current output current.

        Returns:
            float: The measured current in Amperes.
        """
        pass

class SpectrumAnalyzer(InstrumentDriver):
    """Abstract Base Class for Spectrum Analyzers."""
    @abstractmethod
    def peak_search(self):
        """Moves marker to the highest peak."""
        pass

    @abstractmethod
    def get_marker_amplitude(self) -> float:
        """Returns the amplitude at the current marker.

        Returns:
            float: The amplitude value (e.g., in dBm).
        """
        pass

    def get_peak_value(self) -> float:
        """Helper: Performs peak search and returns amplitude.

        Returns:
            float: The peak amplitude value.
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
    def get_trace_data(self, measurement_name: str) -> list[float]:
        """Returns the formatted data trace.

        Args:
            measurement_name (str): The name of the measurement/trace to retrieve.

        Returns:
            list[float]: The trace data points.
        """
        pass

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
    def get_waveform(self, channel: int) -> list[float]:
        """Returns the waveform data for the specified channel.

        Args:
            channel (int): The channel number to read from.

        Returns:
            list[float]: The waveform data points.
        """
        pass
