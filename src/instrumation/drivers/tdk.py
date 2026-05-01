from .base import PowerSupply
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult

@register_driver("PSU")
class TDKLambdaZPlus(RealDriver, PowerSupply):
    """Driver for TDK-Lambda Z+ Series Power Supplies."""

    def preset(self, automation_optimized: bool = True):
        self.write("*RST")
        self.sync_config()

    def set_voltage(self, voltage: float):
        self.safe_send(f":VOLT {voltage}")

    def get_voltage(self) -> float:
        return float(self.query_ascii(":VOLT?"))

    def set_current_limit(self, current: float):
        self.safe_send(f":CURR {current}")

    def get_current(self) -> MeasurementResult:
        val = self.query_ascii(":MEAS:CURR?")
        return MeasurementResult(float(val), "A")

    def set_output(self, state: bool):
        self.write(f":OUTP {'ON' if state else 'OFF'}")

    def get_output(self) -> bool:
        state = self.query_ascii(":OUTP?")
        return state == "1" or state.upper() == "ON"

    def set_ovp(self, voltage: float):
        self.safe_send(f":VOLT:PROT {voltage}")

    def set_ocp(self, current: float):
        self.safe_send(f":CURR:PROT {current}")

    def measure_frequency(self) -> MeasurementResult: return MeasurementResult(0.0, "Hz")
    def measure_duty_cycle(self) -> MeasurementResult: return MeasurementResult(0.0, "%")
    def measure_v_peak_to_peak(self) -> MeasurementResult: return MeasurementResult(0.0, "V")

    def shutdown_safety(self):
        """Safety first: Disable output and zero voltage."""
        self.set_output(False)
        self.set_voltage(0.0)
        self.sync_config()
