from .base import SpectrumAnalyzer, NetworkAnalyzer, SignalGenerator
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult

@register_driver("SA")
class KeysightMXA(RealDriver, SpectrumAnalyzer):
    """Driver for Keysight MXA Series Spectrum Analyzers.

    This driver provides support for basic spectrum analysis functions
    on Keysight MXA instruments.
    """
    def peak_search(self):
        """Performs a peak search and moves Marker 1 to the maximum peak."""
        # Keysight command for Peak Search
        self.inst.write(":CALC:MARK1:MAX") 

    def get_marker_amplitude(self) -> MeasurementResult:
        """Queries the amplitude value of Marker 1.

        Returns:
            MeasurementResult: The amplitude value in dBm.
        """
        # Keysight command to read Y-axis value
        val = self.inst.query(":CALC:MARK1:Y?")
        return MeasurementResult(float(val), "dBm")

@register_driver("NA")
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

    def get_trace_data(self, measurement_name: str) -> MeasurementResult:
        """Selects the measurement and queries the formatted data.

        Args:
            measurement_name (str): The name of the measurement (Trace) to select.

        Returns:
            MeasurementResult: The formatted trace data points.
        """
        # Select the measurement (Trace)
        self.inst.write(f"CALC:PAR:SEL '{measurement_name}'")
        # Query Formatted Data
        data_str = self.inst.query("CALC:DATA? FDATA")
        # Convert comma-separated string to list of floats
        data = [float(x) for x in data_str.split(',')]
        return MeasurementResult(data, "dB")

    def get_complex_trace(self, measurement_name: str) -> MeasurementResult:
        """Selects the measurement and queries the complex (I/Q) data.
        
        Args:
            measurement_name (str): The name of the measurement/trace.
            
        Returns:
            MeasurementResult: The complex data points.
        """
        # Select the measurement (Trace)
        self.inst.write(f"CALC:PAR:SEL '{measurement_name}'")
        # Query Complex Data (SDATA returns Real, Imaginary pairs)
        data_str = self.inst.query("CALC:DATA? SDATA")
        raw_data = [float(x) for x in data_str.split(',')]
        data = [complex(raw_data[i], raw_data[i+1]) for i in range(0, len(raw_data), 2)]
        return MeasurementResult(data, "IQ")

@register_driver("SG")
class KeysightSG(RealDriver, SignalGenerator):
    """Driver for Keysight Signal Generators (EXG/MXG)."""
    def set_frequency(self, hz: float):
        self.inst.write(f":FREQ {hz}")

    def set_amplitude(self, dbm: float):
        self.inst.write(f":POW {dbm}")

    def set_output(self, state: bool):
        val = "ON" if state else "OFF"
        self.inst.write(f":OUTP {val}")