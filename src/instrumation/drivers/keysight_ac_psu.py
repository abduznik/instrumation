from .base import ACPowerSource
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("ACPSU")
class KeysightAC6800B(RealDriver, ACPowerSource):
    """Driver for Keysight AC6800B Series Programmable AC Power Source.

    Single-phase AC/DC output up to 4 kVA. Unlike the DC-only
    `PowerSupply` drivers in this library (e.g. `KeysightE36313A`), the
    AC6800B needs frequency programming and an explicit AC/DC/AC+DC
    output mode alongside the voltage/current setpoints.

    Command Reference (AC6800B Series Programming Guide):
        - SOURce:VOLTage[:LEVel][:IMMediate][:AMPLitude] <v>
        - SOURce:VOLTage? / SOURce:FREQuency <hz> / SOURce:FREQuency?
        - SOURce:VOLTage:MODE {AC|DC|AC+DC} / SOURce:VOLTage:MODE?
        - SOURce:CURRent[:LEVel][:IMMediate][:AMPLitude] <a>
        - SOURce:VOLTage:PROTection[:LEVel] <v>
        - SOURce:CURRent:PROTection[:LEVel] <a>
        - OUTPut[:STATe] {ON|OFF} / OUTPut[:STATe]?
        - OUTPut:PROTection:CLEar
        - MEASure:VOLTage[:AC]? / MEASure:CURRent[:AC]? / MEASure:POWer[:AC]?
        - SOURce:VOLTage:OFFSet <v>                — DC offset (AC+DC mode)
        - *IDN? / *RST / *CLS / *OPC?
    """

    _MODE_MAP = {"AC": "AC", "DC": "DC", "AC+DC": "AC+DC", "ACDC": "AC+DC"}

    def set_voltage(self, volts_rms: float) -> None:
        self.safe_send(f"SOUR:VOLT {volts_rms}")

    def get_voltage(self) -> float:
        return float(self.query_ascii("SOUR:VOLT?"))

    def set_frequency(self, hz: float) -> None:
        self.safe_send(f"SOUR:FREQ {hz}")

    def get_frequency(self) -> float:
        return float(self.query_ascii("SOUR:FREQ?"))

    def set_output_mode(self, mode: str) -> None:
        key = mode.upper()
        if key not in self._MODE_MAP:
            raise ValueError(f"Invalid output mode: {mode}")
        self.safe_send(f"SOUR:VOLT:MODE {self._MODE_MAP[key]}")

    def get_output_mode(self) -> str:
        return self.query_ascii("SOUR:VOLT:MODE?").strip()

    def set_output(self, state: bool) -> None:
        self.safe_send(f"OUTP {'ON' if state else 'OFF'}")

    def get_output(self) -> bool:
        return self.query_ascii("OUTP?").strip() in ("1", "ON")

    def measure_voltage(self) -> MeasurementResult:
        return self._meas("MEAS:VOLT:AC?", "Vrms")

    def measure_current(self) -> MeasurementResult:
        return self._meas("MEAS:CURR:AC?", "Arms")

    def measure_power(self) -> MeasurementResult:
        return self._meas("MEAS:POW:AC?", "W")

    def set_current_limit(self, amps_rms: float) -> None:
        self.safe_send(f"SOUR:CURR {amps_rms}")

    def get_current_limit(self) -> float:
        return float(self.query_ascii("SOUR:CURR?"))

    def set_ovp(self, volts: float) -> None:
        self.safe_send(f"SOUR:VOLT:PROT {volts}")

    def set_ocp(self, amps: float) -> None:
        self.safe_send(f"SOUR:CURR:PROT {amps}")

    def clear_protection(self) -> None:
        self.safe_send("OUTP:PROT:CLE")

    def set_dc_offset(self, volts: float) -> None:
        self.safe_send(f"SOUR:VOLT:OFFS {volts}")

    def get_dc_offset(self) -> float:
        return float(self.query_ascii("SOUR:VOLT:OFFS?"))

    def shutdown_safety(self) -> None:
        self.set_output(False)
        self.set_voltage(0.0)
        self.sync_config()
