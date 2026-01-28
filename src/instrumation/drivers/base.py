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

    @abstractmethod
    def measure_frequency(self) -> float:
        """Measures the frequency of the input signal."""
        pass

    @abstractmethod
    def measure_duty_cycle(self) -> float:
        """Measures the duty cycle of the input signal as a percentage."""
        pass

    @abstractmethod
    def measure_v_peak_to_peak(self) -> float:
        """Measures the peak-to-peak voltage of the input signal."""
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
