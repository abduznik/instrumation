from .base import SpectrumAnalyzer, NetworkAnalyzer
from .real import RealDriver

class KeysightMXA(SpectrumAnalyzer):
    def peak_search(self):
        # Keysight command for Peak Search
        self.inst.write(":CALC:MARK1:MAX") 

    def get_marker_amplitude(self):
        # Keysight command to read Y-axis value
        val = self.inst.query(":CALC:MARK1:Y?")
        return float(val)

class KeysightPNA(RealDriver, NetworkAnalyzer):
    """
    Driver for Keysight PNA Series (e.g., E8363C).
    
    Compatible with newer PNA models (e.g., PNA-X N524x, PNA-L N523x) 
    and ENA models sharing the PNA firmware (e.g., E5080B), 
    as these SCPI commands (SENS:FREQ, CALC:PAR:SEL, CALC:DATA?) are standard.
    """
    def set_start_frequency(self, freq_hz: float):
        self.inst.write(f"SENS:FREQ:STAR {freq_hz}")

    def set_stop_frequency(self, freq_hz: float):
        self.inst.write(f"SENS:FREQ:STOP {freq_hz}")

    def set_points(self, num_points: int):
        self.inst.write(f"SENS:SWE:POIN {num_points}")

    def get_trace_data(self, measurement_name: str) -> list[float]:
        """
        Selects the measurement and queries the formatted data.
        """
        # Select the measurement (Trace)
        self.inst.write(f"CALC:PAR:SEL '{measurement_name}'")
        # Query Formatted Data
        data_str = self.inst.query("CALC:DATA? FDATA")
        # Convert comma-separated string to list of floats
        return [float(x) for x in data_str.split(',')]