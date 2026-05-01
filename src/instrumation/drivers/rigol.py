from .base import SpectrumAnalyzer
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult

@register_driver("SA")
class RigolDSA(RealDriver, SpectrumAnalyzer):
    """Driver for Rigol DSA Series Spectrum Analyzers."""
    
    def preset(self, automation_optimized: bool = True):
        self.write("*RST")
        self.wait_ready()

    def peak_search(self):
        self.safe_send(":CALC:MARK:MAX") 

    def get_marker_amplitude(self) -> MeasurementResult:
        val = self.query_ascii(":CALC:MARK:Y?") 
        return MeasurementResult(float(val), "dBm")

    def set_center_freq(self, hz: float):
        self.safe_send(f":SENS:FREQ:CENT {self.format_frequency(hz)}")

    def set_span(self, hz: float):
        self.safe_send(f":SENS:FREQ:SPAN {hz}")

    def set_rbw(self, hz: float):
        self.safe_send(f":SENS:BAND:RES {hz}")

    def set_vbw(self, hz: float):
        self.safe_send(f":SENS:BAND:VID {hz}")

    def get_trace_data(self) -> MeasurementResult:
        # Optimization: Use binary transfer
        self.write(":FORM:TRAC:DATA REAL")
        data = self.query_binary_values(":TRAC? TRACE1", datatype='f', is_big_endian=False)
        return MeasurementResult(list(data), "dBm")

    def measure_frequency(self) -> MeasurementResult:
        return MeasurementResult(0.0, "Hz")

    def measure_duty_cycle(self) -> MeasurementResult:
        return MeasurementResult(0.0, "%")

    def measure_v_peak_to_peak(self) -> MeasurementResult:
        return MeasurementResult(0.0, "V")

    def shutdown_safety(self):
        self.sync_config()
