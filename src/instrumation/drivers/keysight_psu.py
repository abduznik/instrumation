from .base import PowerSupply
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("PSU")
class KeysightE36313A(RealDriver, PowerSupply):
    """Driver for Keysight E36300 Series Triple-Output DC Power Supplies.

    Validated Model: E36313A. Uses the SCPI-99 channel-list syntax
    ``(@<chanlist>)`` shared with Keysight loads/analyzers -- every
    setpoint/measurement command takes an explicit ``(@<n>)`` argument
    rather than a channel-select round-trip (BK Precision 9130B) or a
    ``CH<n>`` prefix (Rigol DP800/Siglent SPD3303X).

    SCPI Reference (E36300 Series Programming Guide):
        - [SOURce:]VOLTage[:LEVel][:IMMediate][:AMPLitude] <v>, (@<n>)
        - [SOURce:]CURRent[:LEVel][:IMMediate][:AMPLitude] <i>, (@<n>)
        - [SOURce:]VOLTage:PROTection[:LEVel] <v>, (@<n>)
        - [SOURce:]VOLTage:PROTection:CLEar (@<n>)
        - [SOURce:]CURRent:PROTection:STATe {ON|OFF}, (@<n>)
        - OUTPut[:STATe] {ON|OFF}, (@<n>)
        - OUTPut[:STATe]? (@<n>)
        - OUTPut:PAIR {OFF|PARallel|SERies}
        - MEASure[:SCALar]:VOLTage[:DC]? (@<n>)
        - MEASure[:SCALar]:CURRent[:DC]? (@<n>)
        - APPLy P6V|P25V|N25V|CH1|CH2|CH3[,<voltage>[,<current>]]
    """

    CHANNELS = (1, 2, 3)

    def _chan(self, channel: int = None) -> str:
        return f"(@{channel})" if channel else "(@1)"

    def preset(self, automation_optimized: bool = True) -> None:
        self.write("*RST")
        self.sync_config()

    def set_voltage(self, voltage: float, channel: int = None) -> None:
        self.safe_send(f"VOLT {voltage}, {self._chan(channel)}")

    def get_voltage(self, channel: int = None) -> float:
        return float(self.query_ascii(f"VOLT? {self._chan(channel)}"))

    def set_current_limit(self, current: float, channel: int = None) -> None:
        self.safe_send(f"CURR {current}, {self._chan(channel)}")

    def get_current(self, channel: int = None) -> MeasurementResult:
        return self._meas(f"CURR? {self._chan(channel)}", "A")

    def set_output(self, state: bool, channel: int = None) -> None:
        self.write(f"OUTP {'ON' if state else 'OFF'}, {self._chan(channel)}")

    def get_output(self, channel: int = None) -> bool:
        state = self.query_ascii(f"OUTP? {self._chan(channel)}")
        return state.strip() in ("1", "ON")

    def set_ovp(self, voltage: float, channel: int = None) -> None:
        self.write(f"VOLT:PROT {voltage}, {self._chan(channel)}")

    def get_ovp(self, channel: int = None) -> float:
        return float(self.query(f"VOLT:PROT? {self._chan(channel)}"))

    def set_ocp(self, current: float, channel: int = None) -> None:
        self.write(f"CURR:PROT:STAT ON, {self._chan(channel)}")

    def clear_protection(self, channel: int = None) -> None:
        self.write(f"VOLT:PROT:CLE {self._chan(channel)}")
        self.write(f"CURR:PROT:CLE {self._chan(channel)}")

    def measure_voltage_actual(self, channel: int = None) -> MeasurementResult:
        return self._meas(f"MEAS:VOLT? {self._chan(channel)}", "V")

    def measure_current(self, channel: int = None) -> MeasurementResult:
        return self._meas(f"MEAS:CURR? {self._chan(channel)}", "A")

    def set_output_pairing(self, mode: str) -> None:
        """Sets CH1/CH2 pairing: 'OFF', 'PAR' (parallel), or 'SER' (series)."""
        mode_upper = mode.upper()
        if mode_upper not in ("OFF", "PAR", "SER"):
            raise ValueError("mode must be 'OFF', 'PAR', or 'SER'")
        self.write(f"OUTP:PAIR {mode_upper}")

    def shutdown_safety(self) -> None:
        for ch in self.CHANNELS:
            self.set_output(False, channel=ch)
            self.set_voltage(0.0, channel=ch)
        self.sync_config()
