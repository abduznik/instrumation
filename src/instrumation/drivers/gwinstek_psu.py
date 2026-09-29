from .base import PowerSupply
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("PSU")
class GWInstekGPP4323(RealDriver, PowerSupply):
    """Driver for GW Instek GPP Series Multi-Channel DC Power Supplies.

    Validated Model: GPP-4323 (4 independent channels). The GPP dialect
    puts the channel number directly as a numeric suffix on the
    keyword itself -- ``SOURce2:VOLTage``, ``OUTPut2:STATe``,
    ``MEASure2:CURRent?`` -- distinct from the Keysight E36300's
    ``(@<n>)`` channel-list syntax, the Rigol DP800/Siglent SPD3303X
    ``CH<n>:`` prefix, and the BK Precision 9130B's channel-select
    round-trip. Channel 1 may omit its suffix (``SOURce:VOLTage`` ==
    ``SOURce1:VOLTage``); other channels must specify the suffix.

    SCPI Reference (GPP-1326/2323/3323/4323 Series User Manual):
        - SOURce[1|2|3|4]:VOLTage <NRf>
        - SOURce[1|2|3|4]:VOLTage?
        - SOURce[1|2|3|4]:CURRent <NRf>
        - SOURce[1|2|3|4]:CURRent?
        - OUTPut[1|2|3|4][:STATe] {ON|OFF}
        - OUTPut[1|2|3|4][:STATe]?
        - OUTPut[1|2|3|4]:OVP <value> / OUTPut[1|2|3|4]:OVP:STATe {ON|OFF}
        - OUTPut[1|2|3|4]:OCP <value> / OUTPut[1|2|3|4]:OCP:STATe {ON|OFF}
        - MEASure[1|2|3|4]:VOLTage[:DC]?
        - MEASure[1|2|3|4]:CURRent[:DC]?
        - MEASure[1|2|3|4]:POWEr[:DC]?
        - OUTPut:SERies {ON|OFF}[FAST] / OUTPut:PARallel {ON|OFF}[FAST]
    """

    def _n(self, channel: int = None) -> str:
        return str(channel) if channel else "1"

    def preset(self, automation_optimized: bool = True) -> None:
        self.write("*RST")
        self.sync_config()

    def set_voltage(self, voltage: float, channel: int = None) -> None:
        self.safe_send(f"SOUR{self._n(channel)}:VOLT {voltage}")

    def get_voltage(self, channel: int = None) -> float:
        return float(self.query_ascii(f"SOUR{self._n(channel)}:VOLT?"))

    def set_current_limit(self, current: float, channel: int = None) -> None:
        self.safe_send(f"SOUR{self._n(channel)}:CURR {current}")

    def get_current(self, channel: int = None) -> MeasurementResult:
        return self._meas(f"SOUR{self._n(channel)}:CURR?", "A")

    def set_output(self, state: bool, channel: int = None) -> None:
        self.write(f"OUTP{self._n(channel)}:STAT {'ON' if state else 'OFF'}")

    def get_output(self, channel: int = None) -> bool:
        state = self.query_ascii(f"OUTP{self._n(channel)}:STAT?")
        return state.strip().upper() in ("1", "ON")

    def set_ovp(self, voltage: float, channel: int = None) -> None:
        self.write(f"OUTP{self._n(channel)}:OVP {voltage}")
        self.write(f"OUTP{self._n(channel)}:OVP:STAT ON")

    def get_ovp(self, channel: int = None) -> float:
        return float(self.query(f"OUTP{self._n(channel)}:OVP?"))

    def set_ocp(self, current: float, channel: int = None) -> None:
        self.write(f"OUTP{self._n(channel)}:OCP {current}")
        self.write(f"OUTP{self._n(channel)}:OCP:STAT ON")

    def get_ocp(self, channel: int = None) -> float:
        return float(self.query(f"OUTP{self._n(channel)}:OCP?"))

    def clear_protection(self, channel: int = None) -> None:
        self.write(f"OUTP{self._n(channel)}:OVP:STAT OFF")
        self.write(f"OUTP{self._n(channel)}:OCP:STAT OFF")

    def measure_voltage_actual(self, channel: int = None) -> MeasurementResult:
        return self._meas(f"MEAS{self._n(channel)}:VOLT?", "V")

    def measure_current(self, channel: int = None) -> MeasurementResult:
        return self._meas(f"MEAS{self._n(channel)}:CURR?", "A")

    def measure_power(self, channel: int = None) -> MeasurementResult:
        return self._meas(f"MEAS{self._n(channel)}:POW?", "W")

    def set_series_mode(self, state: bool) -> None:
        """Links CH1+CH2 (and CH3+CH4 where present) in series."""
        self.write(f"OUTP:SER {'ON' if state else 'OFF'}")

    def set_parallel_mode(self, state: bool) -> None:
        """Links CH1+CH2 (and CH3+CH4 where present) in parallel."""
        self.write(f"OUTP:PAR {'ON' if state else 'OFF'}")

    def shutdown_safety(self) -> None:
        for ch in (1, 2, 3, 4):
            self.set_output(False, channel=ch)
            self.set_voltage(0.0, channel=ch)
        self.sync_config()
