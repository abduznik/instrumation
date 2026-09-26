from .base import PowerSupply
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("PSU")
class SorensenSG(RealDriver, PowerSupply):
    """Driver for Ametek Sorensen SG/SGA/SGX Series DC Power Supplies.

    Validated Model: SG Series (single output). Full SCPI-99 subsystem,
    directly comparable in dialect to `KeysightE36313A`/`RigolDP832`.

    This initial driver covers the core source/measure/protection
    subsystem only -- the Sorensen-specific ``:PROGram`` subsystem for
    stored multi-step test sequences (a genuinely new interaction
    pattern, not present in any existing `PowerSupply` driver) is
    intentionally out of scope for this pass and can be layered on
    later without touching this interface.

    SCPI Reference (SG Series IEEE 488.2/RS232/Ethernet Programming Manual):
        - :SOURce:VOLTage <v> / :SOURce:VOLTage?
        - :SOURce:CURRent <i> / :SOURce:CURRent?
        - :OUTPut:STATe {ON|OFF} / :OUTPut:STATe?
        - :MEASure:VOLTage? / :MEASure:CURRent?
        - :SOURce:VOLTage:PROTection <v>
        - :SOURce:CURRent:PROTection <i>
        - *IDN? / *RST / SYSTem:ERRor?
    """

    def set_voltage(self, voltage: float) -> None:
        self.safe_send(f"SOUR:VOLT {voltage}")

    def get_voltage(self) -> float:
        return float(self.query_ascii("SOUR:VOLT?"))

    def set_current_limit(self, current: float) -> None:
        self.safe_send(f"SOUR:CURR {current}")

    def get_current(self) -> MeasurementResult:
        return self._meas("SOUR:CURR?", "A")

    def set_output(self, state: bool) -> None:
        self.safe_send(f"OUTP:STAT {'ON' if state else 'OFF'}")

    def get_output(self) -> bool:
        return self.query_ascii("OUTP:STAT?").strip() in ("1", "ON")

    def set_ovp(self, voltage: float) -> None:
        self.safe_send(f"SOUR:VOLT:PROT {voltage}")

    def set_ocp(self, current: float) -> None:
        self.safe_send(f"SOUR:CURR:PROT {current}")

    def clear_protection(self) -> None:
        self.safe_send("OUTP:PROT:CLE")

    def measure_voltage_actual(self) -> MeasurementResult:
        return self._meas("MEAS:VOLT?", "V")

    def measure_current(self) -> MeasurementResult:
        return self._meas("MEAS:CURR?", "A")

    def shutdown_safety(self) -> None:
        self.set_output(False)
        self.set_voltage(0.0)
        self.sync_config()
