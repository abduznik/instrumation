from .base import Oscilloscope
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("SCOPE")
class RigolMSO5000(RealDriver, Oscilloscope):
    """Driver for Rigol MSO5000 Series Mixed-Signal Oscilloscopes.

    Validated Model: MSO5354 (4 analog + 16 digital channels). Basic
    control (`:RUN`/`:STOP`/`:SINGle`/`:AUToscale`) matches the
    MSO1000Z/DS1000Z family already covered by ``RigolDS1054Z``, but
    the measurement subsystem differs: ``:MEASure:ITEM? <item>,<src>``
    takes the source as an explicit second argument on every query
    rather than DS1000Z's ``:MEASure:FREQuency? CHANnel<n>`` per-item
    query form. LA (logic analyzer), protocol decode, and mask-test
    features from the Programming Guide are not implemented here.

    SCPI Reference (MSO5000 Series Programming Guide):
        - :RUN / :STOP / :SINGle / :AUTOscale / :TFORce
        - :TRIGger:EDGE:SOURce <src> / :TRIGger:EDGE:LEVel <v> /
          :TRIGger:EDGE:SLOPe {POSitive|NEGative|RFALl}
        - :WAVeform:SOURce <src> / :WAVeform:FORMat {WORD|BYTE|ASCii}
        - :WAVeform:DATA?
        - :MEASure:ITEM? <item>,<src>   — item in {FREQuency|PDUTy|VPP|...}
        - :DISPlay:DATA? PNG,COLor      — screenshot capture
    """

    def __init__(self, resource: str, rm=None) -> None:
        super().__init__(resource, rm)
        self.max_voltage = 40.0
        self._channel_count = 4

    def run(self) -> None:
        self.write(":RUN")

    def stop(self) -> None:
        self.write(":STOP")

    def single(self) -> None:
        self.write(":SINGle")

    def auto_scale(self) -> None:
        self.write(":AUTOscale")
        self.wait_ready()

    def set_trigger(self, source: str, level: float, slope: str) -> None:
        self.safe_send(":TRIGger:MODE EDGE")
        self.safe_send(f":TRIGger:EDGE:SOURce {source}")
        self.safe_send(f":TRIGger:EDGE:LEVel {level}")
        slope_map = {"POSITIVE": "POSitive", "NEGATIVE": "NEGative", "RFALL": "RFALl"}
        self.safe_send(f":TRIGger:EDGE:SLOPe {slope_map.get(slope.upper(), slope)}")

    def get_waveform(self, channel: int) -> MeasurementResult:
        self.safe_send(f":WAVeform:SOURce CHANnel{channel}")
        self.safe_send(":WAVeform:FORMat BYTE")
        raw = self.query_binary_values(":WAVeform:DATA?", datatype='B')
        return MeasurementResult([float(v) for v in raw], "V", channel=channel)

    def get_screenshot(self) -> bytes:
        self.write(":DISPlay:DATA? PNG,COLor")
        return self.inst.read_raw()

    def _measure_item(self, item: str, channel: int) -> float:
        val = self.query_ascii(f":MEASure:ITEM? {item},CHANnel{channel}")
        try:
            return float(val)
        except ValueError:
            return 0.0

    def measure_frequency(self, channel: int = 1) -> MeasurementResult:
        return MeasurementResult(self._measure_item("FREQuency", channel), "Hz", channel=channel)

    def measure_duty_cycle(self, channel: int = 1) -> MeasurementResult:
        return MeasurementResult(self._measure_item("PDUTy", channel), "%", channel=channel)

    def measure_v_peak_to_peak(self, channel: int = 1) -> MeasurementResult:
        return MeasurementResult(self._measure_item("VPP", channel), "V", channel=channel)

    def shutdown_safety(self) -> None:
        self.stop()
        self.sync_config()
