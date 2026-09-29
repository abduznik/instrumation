from .base import PowerSupply
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("PSU")
class Agilent6632B(RealDriver, PowerSupply):
    """Driver for Agilent/HP 6632B/6634B System DC Power Supplies.

    Validated Model: 6632B (single output). Shares its SCPI-99 lineage
    with the rest of the 6631B-6634B family and the current Keysight
    dialect (`Keysight34461A`, `KeysightPNA`) -- one of the earliest
    fully SCPI-compliant Agilent/HP PSU families, still common in
    legacy ATE racks.

    SCPI Reference (663xB GPIB Programming Guide):
        - VOLT <v> / VOLT?
        - CURR <i> / CURR?
        - OUTP {ON|OFF} / OUTP?
        - MEAS:VOLT? / MEAS:CURR?
        - VOLT:PROT <v> / VOLT:PROT?
        - CURR:PROT:STAT {ON|OFF} / CURR:PROT:STAT?
        - OUTP:PON:STAT {RST|RCL0}   — power-on state configuration
        - *IDN? / *RST / SYST:ERR?
    """

    def set_voltage(self, voltage: float) -> None:
        self.safe_send(f"VOLT {voltage}")

    def get_voltage(self) -> float:
        return float(self.query_ascii("VOLT?"))

    def set_current_limit(self, current: float) -> None:
        self.safe_send(f"CURR {current}")

    def get_current(self) -> MeasurementResult:
        return self._meas("CURR?", "A")

    def set_output(self, state: bool) -> None:
        self.safe_send(f"OUTP {'ON' if state else 'OFF'}")

    def get_output(self) -> bool:
        return self.query_ascii("OUTP?").strip() in ("1", "ON")

    def set_ovp(self, voltage: float) -> None:
        self.safe_send(f"VOLT:PROT {voltage}")

    def set_ocp(self, current: float) -> None:
        self.set_current_limit(current)
        self.safe_send("CURR:PROT:STAT ON")

    def clear_protection(self) -> None:
        self.safe_send("OUTP:PROT:CLE")

    def measure_voltage_actual(self) -> MeasurementResult:
        return self._meas("MEAS:VOLT?", "V")

    def measure_current(self) -> MeasurementResult:
        return self._meas("MEAS:CURR?", "A")

    def set_autostart(self, state: bool) -> None:
        """Sets the power-on state: RCL0 (last state) if True, RST (reset defaults) if False."""
        self.safe_send(f"OUTP:PON:STAT {'RCL0' if state else 'RST'}")

    def shutdown_safety(self) -> None:
        self.set_output(False)
        self.set_voltage(0.0)
        self.sync_config()
