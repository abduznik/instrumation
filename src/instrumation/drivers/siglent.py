from .base import Oscilloscope
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult

@register_driver("SCOPE")
class SiglentSDS(RealDriver, Oscilloscope):
    """Refined Driver for Siglent SDS Series Oscilloscopes."""

    def preset(self, automation_optimized: bool = True):
        self.write("*RST")
        self.wait_ready()

    def run(self): self.write("ARM")
    def stop(self): self.write("STOP")
    def single(self): self.write("SING")

    def get_waveform(self, channel: int) -> MeasurementResult:
        self.write(f"C{channel}:WF? DAT2")
        prefix = f"C{channel}:WF DAT2,"
        self.inst.read_bytes(len(prefix))
        data = self.inst.query_binary_values("", datatype='b', container=list)
        return MeasurementResult([float(b) for b in data], "V")

    def auto_scale(self):
        self.safe_send("AUTOSCALE")

    def set_trigger(self, source: str, level: float, slope: str):
        self.safe_send(f"TRSE EDGE,SR,{source},HT,OFF")
        self.safe_send(f"{source}:TRLV {level}V")
        self.safe_send(f"{source}:TRSL {slope.upper()}")

    def get_screenshot(self) -> bytes:
        self.write("SCDP")
        return self.inst.read_raw()

    def _measure_pava(self, channel: int, param: str) -> float:
        resp = self.query_ascii(f"C{channel}:PAVA? {param}")
        # Parse "CHx:PAVA param,value unit"
        try:
            val_part = resp.split(',')[-1]
            # Remove unit (Hz, V, %, etc)
            val_str = "".join([c for c in val_part if c.isdigit() or c in ".-eE"])
            return float(val_str)
        except:
            return 0.0

    def measure_frequency(self, channel: int = 1) -> MeasurementResult:
        val = self._measure_pava(channel, "FREQ")
        return MeasurementResult(val, "Hz")

    def measure_duty_cycle(self, channel: int = 1) -> MeasurementResult:
        val = self._measure_pava(channel, "DUTY")
        return MeasurementResult(val, "%")

    def measure_v_peak_to_peak(self, channel: int = 1) -> MeasurementResult:
        val = self._measure_pava(channel, "PKPK")
        return MeasurementResult(val, "V")

    def shutdown_safety(self):
        self.stop()
        self.sync_config()
