from .base import ElectronicLoad
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("LOAD")
@register_driver("ELOAD")
class Chroma63200A(RealDriver, ElectronicLoad):
    """Driver for Chroma 63200A Series High-Power Programmable DC Electronic Loads.

    Validated Model: 63200A series (e.g. 63204A). This is the most
    distinctive dialect of any electronic load in this library: a
    single ``MODE`` mnemonic encodes BOTH the operating mode and the
    measurement range in one token -- ``MODE CCH`` (CC, High range),
    ``MODE CVL`` (CV, Low range), etc. This driver always selects the
    **High** range variant (``CCH``/``CVH``/``CRH``/``CPH``) for
    ``set_mode()`` since it's the safest default for an unknown DUT;
    call ``write("MODE CCL")``/``write("MODE CCM")`` directly for
    Low/Middle range. Setpoints use the ``<FUNC>:STATic:L1`` level-1
    static value (the front panel's "A" state); the ``L2``/"B" state
    and slew-rate (`RISE`/`FALL`) parameters are not wired up here.

    SCPI Reference (63200A Series Operation & Programming Manual):
        - MODE {CCL|CCM|CCH|CRL|CRM|CRH|CVL|CVM|CVH|CPL|CPM|CPH|...}
        - MODE?
        - CURRent:STATic:L1 <amps> / CURRent:STATic:L1?
        - VOLTage:STATic:L1 <volts> / VOLTage:STATic:L1?
        - RESistance:STATic:L1 <ohms> / RESistance:STATic:L1?
        - POWer:STATic:L1 <watts> / POWer:STATic:L1?
        - LOAD[:STATe] {ON|OFF|0|1}
        - LOAD[:STATe]?
        - LOAD:SHORt[:STATe] {ON|OFF}   — simulated short-circuit
        - LOAD:PROTection?              — protection trip status
        - LOAD:PROTection:CLEar
        - MEASure:VOLTage? / MEASure:CURRent? / MEASure:POWer?

    Unsupported: set_ovp (no dedicated software OVP command), set_ocp/set_opp (OCP/OPP are dedicated MODEs, not trip-level commands).
    """

    _MODE_MAP = {"CC": "CCH", "CV": "CVH", "CR": "CRH", "CP": "CPH"}
    _MODE_MAP_REV = {v: k for k, v in _MODE_MAP.items()}

    def set_mode(self, mode: str) -> None:
        mode_upper = mode.upper()
        if mode_upper not in self._MODE_MAP:
            raise ValueError(f"Invalid mode: {mode}")
        self.safe_send(f"MODE {self._MODE_MAP[mode_upper]}")

    def get_mode(self) -> str:
        scpi_mode = self.query_ascii("MODE?").strip().upper()
        return self._MODE_MAP_REV.get(scpi_mode, scpi_mode)

    def set_current(self, amps: float) -> None:
        self.safe_send(f"CURR:STAT:L1 {amps}")

    def get_current(self) -> float:
        return float(self.query_ascii("CURR:STAT:L1?"))

    def set_voltage(self, volts: float) -> None:
        self.safe_send(f"VOLT:STAT:L1 {volts}")

    def get_voltage(self) -> float:
        return float(self.query_ascii("VOLT:STAT:L1?"))

    def set_resistance(self, ohms: float) -> None:
        self.safe_send(f"RES:STAT:L1 {ohms}")

    def get_resistance(self) -> float:
        return float(self.query_ascii("RES:STAT:L1?"))

    def set_power(self, watts: float) -> None:
        self.safe_send(f"POW:STAT:L1 {watts}")

    def get_power(self) -> float:
        return float(self.query_ascii("POW:STAT:L1?"))

    def set_input(self, state: bool) -> None:
        self.safe_send(f"LOAD {'ON' if state else 'OFF'}")

    def get_input(self) -> bool:
        return self.query_ascii("LOAD?").strip() in ("1", "ON")

    def set_short_circuit(self, state: bool) -> None:
        """Enables/disables the simulated short-circuit input state."""
        self.safe_send(f"LOAD:SHOR {'ON' if state else 'OFF'}")

    def measure_voltage(self) -> MeasurementResult:
        return self._meas("MEAS:VOLT?", "V")

    def measure_current(self) -> MeasurementResult:
        return self._meas("MEAS:CURR?", "A")

    def measure_power(self) -> MeasurementResult:
        return self._meas("MEAS:POW?", "W")

    def measure_resistance(self) -> MeasurementResult:
        self._unsupported_feature("measure_resistance (63200A has no direct MEAS:RES? query)")
        return MeasurementResult(0.0, "Ohm")

    def get_protection_status(self) -> str:
        """Returns the protection status flags reported by LOAD:PROTection?."""
        return self.query_ascii("LOAD:PROT?").strip()

    def clear_protection(self) -> None:
        self.safe_send("LOAD:PROT:CLE")

    def shutdown_safety(self) -> None:
        self.set_input(False)
        self.sync_config()
