from .base import SpectrumAnalyzer, NetworkAnalyzer
from .real import RealDriver

class KeysightMXA(SpectrumAnalyzer):
    """Driver for Keysight MXA Series Spectrum Analyzers.

    This driver provides support for basic spectrum analysis functions
    on Keysight MXA instruments.
    """
    def peak_search(self):
        """Performs a peak search and moves Marker 1 to the maximum peak."""
        # Keysight command for Peak Search
        self.inst.write(":CALC:MARK1:MAX") 

    def get_marker_amplitude(self) -> float:
        """Queries the amplitude value of Marker 1.

        Returns:
            float: The amplitude value in dBm.
        """
        # Keysight command to read Y-axis value
        val = self.inst.query(":CALC:MARK1:Y?")
        return float(val)

class KeysightPNA(RealDriver, NetworkAnalyzer):
    """Driver for Keysight PNA Series (e.g., E8363C).

    Compatible with newer PNA models (e.g., PNA-X N524x, PNA-L N523x) 
    and ENA models sharing the PNA firmware (e.g., E5080B), 
    as these SCPI commands (SENS:FREQ, CALC:PAR:SEL, CALC:DATA?) are standard.
    """
    def set_start_frequency(self, freq_hz: float):
        """Sets the start frequency of the sweep.

        Args:
            freq_hz (float): The start frequency in Hz.
        """
        self.inst.write(f"SENS:FREQ:STAR {freq_hz}")

    def set_stop_frequency(self, freq_hz: float):
        """Sets the stop frequency of the sweep.

        Args:
            freq_hz (float): The stop frequency in Hz.
        """
        self.inst.write(f"SENS:FREQ:STOP {freq_hz}")

    def set_points(self, num_points: int):
        """Sets the number of data points for the sweep.

        Args:
            num_points (int): The number of points (e.g., 201, 401).
        """
        self.inst.write(f"SENS:SWE:POIN {num_points}")

    def get_trace_data(self, measurement_name: str) -> list[float]:
        """Selects the measurement and queries the formatted data.

        Args:
            measurement_name (str): The name of the measurement (Trace) to select.

        Returns:
            list[float]: The formatted trace data points.
        """
        # Select the measurement (Trace)
        self.inst.write(f"CALC:PAR:SEL '{measurement_name}'")
        # Query Formatted Data
        data_str = self.inst.query("CALC:DATA? FDATA")
        # Convert comma-separated string to list of floats
        return [float(x) for x in data_str.split(',')]