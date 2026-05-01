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
        data_str = self.query_ascii(":TRAC? TRACE1")
        data = [float(x) for x in data_str.split(',')]
        return MeasurementResult(data, "dBm")

    def measure_frequency(self) -> MeasurementResult:
        return MeasurementResult(0.0, "Hz")

    def measure_duty_cycle(self) -> MeasurementResult:
        return MeasurementResult(0.0, "%")

    def measure_v_peak_to_peak(self) -> MeasurementResult:
        return MeasurementResult(0.0, "V")

    def shutdown_safety(self):
        self.sync_config()
