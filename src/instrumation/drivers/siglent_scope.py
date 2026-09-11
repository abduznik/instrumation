from .base import Oscilloscope
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("SCOPE")
class SiglentSDS2000XPlus(RealDriver, Oscilloscope):
    """Driver for Siglent SDS2000X Plus Series Digital Oscilloscopes.

    Validated Model: SDS2000X Plus. Uses the newer standard
    ``:SUBsystem:keyword`` command set documented in the SDS Series
    Programming Guide (EN11D+) -- distinct from the legacy
    ``SiglentSDS`` driver's older ``ARM``/``TRSE``/``C<n>:PAVA?``
    command shapes still used by the original SDS1000/SDS2000X(-E).

    SCPI Reference (SDS Series Programming Guide):
        - :TRIGger:RUN / :TRIGger:STOP
        - :TRIGger:MODE {SINGle|NORMal|AUTO|FTRIG}
        - :TRIGger:EDGE:SOURce <src> / :TRIGger:EDGE:LEVel <v> /
          :TRIGger:EDGE:SLOPe {RISing|FALLing|ALTernate}
        - :AUToset
        - :WAVeform:SOURce <src> / :WAVeform:DATA?  — #N<digits> binary block
        - :MEASure:SIMPle:VALue? <type>  — direct query, e.g. FREQ/DUTY/PKPK
        - :PRINt? {BMP|PNG}
    """

    def preset(self, automation_optimized: bool = True) -> None:
        self.write("*RST")
        self.wait_ready()

    def run(self) -> None:
        self.write(":TRIG:RUN")

    def stop(self) -> None:
        self.write(":TRIG:STOP")

    def single(self) -> None:
        self.write(":TRIG:MODE SINGLE")

    def get_waveform(self, channel: int) -> MeasurementResult:
        self.write(f":WAV:SOUR C{channel}")
        raw = self.query_binary_values(":WAV:DATA?", datatype='B')
        return MeasurementResult([float(b) for b in raw], "V")

    def auto_scale(self) -> None:
        self.safe_send(":AUT")

    def set_trigger(self, source: str, level: float, slope: str) -> None:
        self.safe_send(f":TRIG:EDGE:SOUR {source}")
        self.safe_send(f":TRIG:EDGE:LEV {level}")
        slope_map = {"RISING": "RISING", "FALLING": "FALLING", "ALTERNATE": "ALTERNATE"}
        self.safe_send(f":TRIG:EDGE:SLOP {slope_map.get(slope.upper(), slope.upper())}")

    def get_screenshot(self) -> bytes:
        self.write(":PRIN? PNG")
        return self.inst.read_raw()

    def _measure_simple(self, channel: int, param: str) -> float:
        self.write(f":MEAS:SIMP:SOUR C{channel}")
        val = self.query_ascii(f":MEAS:SIMP:VAL? {param}")
        try:
            return float(val)
        except ValueError:
            return 0.0

    def measure_frequency(self, channel: int = 1) -> MeasurementResult:
        return MeasurementResult(self._measure_simple(channel, "FREQ"), "Hz")

    def measure_duty_cycle(self, channel: int = 1) -> MeasurementResult:
        return MeasurementResult(self._measure_simple(channel, "DUTY"), "%")

    def measure_v_peak_to_peak(self, channel: int = 1) -> MeasurementResult:
        return MeasurementResult(self._measure_simple(channel, "PKPK"), "V")

    def shutdown_safety(self) -> None:
        self.stop()
        self.sync_config()
