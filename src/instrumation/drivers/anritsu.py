from .base import SpectrumAnalyzer, NetworkAnalyzer
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult

@register_driver("SA")
class AnritsuSA(RealDriver, SpectrumAnalyzer):
    """Generic Driver for Anritsu Spectrum Analyzers."""
    
    def preset(self, automation_optimized: bool = True):
        self.write("*RST")
        self.wait_ready()

    def peak_search(self):
        self.safe_send(":CALC:MARK1:MAX") 

    def get_marker_amplitude(self) -> MeasurementResult:
        val = self.query_ascii(":CALC:MARK1:Y?")
        return MeasurementResult(float(val), "dBm")

    def set_center_freq(self, hz: float):
        self.safe_send(f":FREQ:CENT {self.format_frequency(hz)}")

    def set_span(self, hz: float):
        self.safe_send(f":FREQ:SPAN {self.format_frequency(hz)}")

    def set_rbw(self, hz: float):
        self.safe_send(f":BAND {self.format_frequency(hz)}")

    def set_vbw(self, hz: float):
        self.safe_send(f":BAND:VID {self.format_frequency(hz)}")

    def get_trace_data(self) -> MeasurementResult:
        data_str = self.query_ascii(":TRAC? TRACE1")
        data = [float(x) for x in data_str.split(',')]
        return MeasurementResult(data, "dBm")

    def shutdown_safety(self):
        self.sync_config()

@register_driver("NA")
class AnritsuVNA(RealDriver, NetworkAnalyzer):
    """Generic Driver for Anritsu Vector Network Analyzers (ShockLine/VNA Master)."""
    
    def preset(self, automation_optimized: bool = True):
        self.write("*RST")
        self.wait_ready()

    def set_start_frequency(self, freq_hz: float):
        self.safe_send(f":SENS:FREQ:STAR {freq_hz}")

    def set_stop_frequency(self, freq_hz: float):
        self.safe_send(f":SENS:FREQ:STOP {freq_hz}")

    def set_points(self, num_points: int):
        self.safe_send(f":SENS:SWE:POIN {num_points}")

    def get_trace_data(self, measurement_name: str) -> MeasurementResult:
        self.safe_send(f":CALC:PAR:SEL '{measurement_name}'")
        data_str = self.query_ascii(":CALC:DATA? FDATA")
        data = [float(x) for x in data_str.split(',')]
        return MeasurementResult(data, "dB")

    def get_complex_trace(self, measurement_name: str) -> MeasurementResult:
        self.safe_send(f":CALC:PAR:SEL '{measurement_name}'")
        data_str = self.query_ascii(":CALC:DATA? SDATA")
        raw_data = [float(x) for x in data_str.split(',')]
        data = [complex(raw_data[i], raw_data[i+1]) for i in range(0, len(raw_data), 2)]
        return MeasurementResult(data, "IQ")
