from .base import SpectrumAnalyzer
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("SA")
class SiglentSSA3000X(RealDriver, SpectrumAnalyzer):
    """Driver for Siglent SSA3000X Series Spectrum Analyzers.

    Standard SCPI-99 spectrum-analyzer subsystem, the same command
    shape as ``RigolDSA``/``AnritsuSA``.

    SCPI Reference (SSA3000X Series Programming Guide):
        - :SENSe:FREQuency:CENTer <freq> / :SENSe:FREQuency:CENTer?
        - :SENSe:FREQuency:SPAN <freq> / :SENSe:FREQuency:SPAN?
        - :SENSe:BANDwidth[:RESolution] <freq>
        - :SENSe:BANDwidth:VIDeo <freq>
        - :DISPlay:WINDow:TRACe:Y[:SCALe]:RLEVel <dBm>
        - :CALCulate:MARKer[1]:MAXimum      — peak search
        - :CALCulate:MARKer[1]:Y?            — marker amplitude query
        - :TRACe:DATA? 1                     — trace data
    """

    def peak_search(self) -> None:
        self.safe_send(":CALC:MARK1:MAX")

    def get_marker_amplitude(self) -> MeasurementResult:
        return self._meas(":CALC:MARK1:Y?", "dBm")

    def set_center_freq(self, hz: float) -> None:
        self.safe_send(f":SENS:FREQ:CENT {self.format_frequency(hz)}")

    def get_center_freq(self) -> float:
        return float(self.query(":SENS:FREQ:CENT?"))

    def set_span(self, hz: float) -> None:
        self.safe_send(f":SENS:FREQ:SPAN {hz}")

    def get_span(self) -> float:
        return float(self.query(":SENS:FREQ:SPAN?"))

    def set_rbw(self, hz: float) -> None:
        self.safe_send(f":SENS:BAND:RES {hz}")

    def set_vbw(self, hz: float) -> None:
        self.safe_send(f":SENS:BAND:VID {hz}")

    def set_ref_level(self, dbm: float) -> None:
        self.write(f":DISP:WIND:TRAC:Y:RLEV {dbm}")

    def get_trace_data(self) -> MeasurementResult:
        data = self.query_ascii(":TRAC:DATA? 1")
        values = [float(v) for v in data.split(",") if v.strip()]
        return MeasurementResult(values, "dBm")

    def shutdown_safety(self) -> None:
        self.sync_config()
