from .base import Oscilloscope
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult

@register_driver("SCOPE")
class TektronixTDS(RealDriver, Oscilloscope):
    """Refined Driver for Tektronix TDS Series Oscilloscopes."""

    def preset(self, automation_optimized: bool = True):
        self.write("*RST")
        self.wait_ready()

    def run(self): self.write(":ACQUIRE:STATE ON")
    def stop(self): self.write(":ACQUIRE:STATE OFF")
    def single(self):
        self.write(":ACQUIRE:STOPAFTER SEQUENCE")
        self.write(":ACQUIRE:STATE ON")

    def get_waveform(self, channel: int) -> MeasurementResult:
        self.write(f":DATA:SOURCE CH{channel}")
        self.write(":DATA:ENC ASC")
        self.write(":DATA:WIDTH 1")
        raw_data = self.query_ascii(":CURVE?")
        data = [float(x) for x in raw_data.split(',')]
        return MeasurementResult(data, "V")

    def auto_scale(self):
        self.safe_send("AUTOSC")

    def set_trigger(self, source: str, level: float, slope: str):
        self.safe_send(f"TRIG:MAIN:EDGE:SOURCE {source}")
        self.safe_send(f"TRIG:MAIN:LEVEL {level}")
        self.safe_send(f"TRIG:MAIN:EDGE:SLOPE {slope.upper()}")

    def get_screenshot(self) -> bytes:
        self.write("HARDCOPY START")
        return b"TEK_SCREENSHOT_DATA"

    def _measure_imm(self, channel: int, measure_type: str) -> float:
        self.safe_send(f":MEASUREMENT:IMMED:SOURCE CH{channel}")
        self.safe_send(f":MEASUREMENT:IMMED:TYPE {measure_type}")
        val = self.query_ascii(":MEASUREMENT:IMMED:VALUE?")
        return float(val)

    def measure_frequency(self, channel: int = 1) -> MeasurementResult:
        val = self._measure_imm(channel, "FREQUENCY")
        return MeasurementResult(val, "Hz")

    def measure_duty_cycle(self, channel: int = 1) -> MeasurementResult:
        val = self._measure_imm(channel, "DUTY")
        return MeasurementResult(val, "%")

    def measure_v_peak_to_peak(self, channel: int = 1) -> MeasurementResult:
        val = self._measure_imm(channel, "PKPK")
        return MeasurementResult(val, "V")

    def shutdown_safety(self):
        self.stop()
        self.sync_config()
