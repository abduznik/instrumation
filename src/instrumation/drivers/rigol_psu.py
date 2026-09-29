from .base import PowerSupply
from .registry import register_driver
from .real import RealDriver, SaveRecallSlots
from ..results import MeasurementResult


@register_driver("PSU")
class RigolDP832(SaveRecallSlots, RealDriver, PowerSupply):
    """Driver for Rigol DP800 Series Triple-Output DC Power Supplies.

    Validated Model: DP832. Unlike the BK Precision 9130B's
    ``INST:NSEL``-then-plain-command style, DP800 series commands
    address a channel directly via a ``[:SOURce<n>]`` numeric suffix
    (1|2|3) or an explicit ``CH1|CH2|CH3`` argument on ``:OUTPut``/
    ``:MEASure`` -- no channel-select round-trip is required. All
    ``PowerSupply`` interface methods accept an optional ``channel=``
    (defaults to 1).

    SCPI Reference (DP800 Series Programming Guide):
        - [:SOURce<n>]:VOLTage[:LEVel][:IMMediate][:AMPLitude] {<v>|MIN|MAX}
        - [:SOURce<n>]:VOLTage[:LEVel][:IMMediate][:AMPLitude]?
        - [:SOURce<n>]:CURRent[:LEVel][:IMMediate][:AMPLitude] {<i>|MIN|MAX}
        - [:SOURce<n>]:CURRent[:LEVel][:IMMediate][:AMPLitude]?
        - [:SOURce<n>]:VOLTage:PROTection[:LEVel] {<v>|MIN|MAX}
        - [:SOURce<n>]:VOLTage:PROTection:STATe {ON|OFF}
        - [:SOURce<n>]:CURRent:PROTection[:LEVel] {<i>|MIN|MAX}
        - [:SOURce<n>]:CURRent:PROTection:STATe {ON|OFF}
        - :OUTPut[:STATe] [CH1|CH2|CH3,]{ON|OFF}
        - :OUTPut[:STATe]? [CH1|CH2|CH3]
        - :OUTPut:TRACk {CH1|CH2|CH3},{ON|OFF}  — link CH2/CH3 (tracking)
        - :MEASure[:VOLTage][:DC]? [CH1|CH2|CH3]
        - :MEASure:CURRent[:DC]? [CH1|CH2|CH3]
        - :MEASure:POWEr[:DC]? [CH1|CH2|CH3]
        - :INSTrument:NSELect {1|2|3}
        - *SAV {1-10} / *RCL {1-10}
    """

    STATE_SLOTS = range(1, 11)

    def _ch(self, channel: int = None) -> str:
        return f"CH{channel}" if channel else "CH1"

    def _src(self, channel: int = None) -> str:
        return f"SOUR{channel}" if channel else "SOUR1"

    def preset(self, automation_optimized: bool = True) -> None:
        self.write("*RST")
        self.sync_config()

    def set_voltage(self, voltage: float, channel: int = None) -> None:
        self.safe_send(f"{self._src(channel)}:VOLT {voltage}")

    def get_voltage(self, channel: int = None) -> float:
        return float(self.query_ascii(f"{self._src(channel)}:VOLT?"))

    def set_current_limit(self, current: float, channel: int = None) -> None:
        self.safe_send(f"{self._src(channel)}:CURR {current}")

    def get_current(self, channel: int = None) -> MeasurementResult:
        return self._meas(f"{self._src(channel)}:CURR?", "A")

    def set_output(self, state: bool, channel: int = None) -> None:
        self.write(f"OUTP {self._ch(channel)},{'ON' if state else 'OFF'}")

    def get_output(self, channel: int = None) -> bool:
        state = self.query_ascii(f"OUTP? {self._ch(channel)}")
        return state.strip().upper() == "ON"

    def set_ovp(self, voltage: float, channel: int = None) -> None:
        self.write(f"{self._src(channel)}:VOLT:PROT {voltage}")
        self.write(f"{self._src(channel)}:VOLT:PROT:STAT ON")

    def get_ovp(self, channel: int = None) -> float:
        return float(self.query(f"{self._src(channel)}:VOLT:PROT?"))

    def set_ocp(self, current: float, channel: int = None) -> None:
        self.write(f"{self._src(channel)}:CURR:PROT {current}")
        self.write(f"{self._src(channel)}:CURR:PROT:STAT ON")

    def get_ocp(self, channel: int = None) -> float:
        return float(self.query(f"{self._src(channel)}:CURR:PROT?"))

    def clear_protection(self, channel: int = None) -> None:
        self.write(f"{self._src(channel)}:VOLT:PROT:CLE")
        self.write(f"{self._src(channel)}:CURR:PROT:CLE")

    def measure_voltage_actual(self, channel: int = None) -> MeasurementResult:
        return self._meas(f"MEAS:VOLT? {self._ch(channel)}", "V")

    def measure_current(self, channel: int = None) -> MeasurementResult:
        return self._meas(f"MEAS:CURR? {self._ch(channel)}", "A")

    def measure_power(self, channel: int = None) -> MeasurementResult:
        return self._meas(f"MEAS:POWE? {self._ch(channel)}", "W")

    def set_tracking_mode(self, enable: bool, channel: int = None) -> None:
        """Enables/disables output tracking for the given channel (CH2/CH3)."""
        self.write(f"OUTP:TRAC {self._ch(channel)},{'ON' if enable else 'OFF'}")

    def shutdown_safety(self) -> None:
        for ch in (1, 2, 3):
            self.set_output(False, channel=ch)
            self.set_voltage(0.0, channel=ch)
        self.sync_config()
