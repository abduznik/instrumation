from abc import ABC, abstractmethod

class InstrumentDriver(ABC):
    """
    Abstract Base Class for Generic Instruments.
    """
    def __init__(self, resource):
        self.resource = resource
        self.connected = False

    @abstractmethod
    def connect(self):
        """Establishes connection to the instrument."""
        pass

    @abstractmethod
    def disconnect(self):
        """Closes the connection."""
        pass

    @abstractmethod
    def get_id(self) -> str:
        """Returns the identification string of the instrument."""
        pass

class Multimeter(InstrumentDriver):
    """Abstract Base Class for Digital Multimeters."""
    @abstractmethod
    def measure_voltage(self) -> float:
        pass
    
    @abstractmethod
    def measure_resistance(self) -> float:
        pass

class PowerSupply(InstrumentDriver):
    """Abstract Base Class for DC Power Supplies."""
    @abstractmethod
    def set_voltage(self, voltage: float):
        pass
    
    @abstractmethod
    def get_current(self) -> float:
        pass

class SpectrumAnalyzer(InstrumentDriver):
    """Abstract Base Class for Spectrum Analyzers."""
    @abstractmethod
    def peak_search(self):
        """Moves marker to the highest peak."""
        pass

    @abstractmethod
    def get_marker_amplitude(self) -> float:
        """Returns the amplitude at the current marker."""
        pass

    def get_peak_value(self) -> float:
        """Helper: Performs peak search and returns amplitude."""
        self.peak_search()
        return self.get_marker_amplitude()

class NetworkAnalyzer(InstrumentDriver):
    """Abstract Base Class for Vector Network Analyzers."""
    @abstractmethod
    def set_start_frequency(self, freq_hz: float):
        pass

    @abstractmethod
    def set_stop_frequency(self, freq_hz: float):
        pass

    @abstractmethod
    def set_points(self, num_points: int):
        pass

    @abstractmethod
    def get_trace_data(self, measurement_name: str) -> list[float]:
        """Returns the formatted data trace."""
        pass
