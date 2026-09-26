from .base import ElectronicLoad
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("LOAD")
@register_driver("ELOAD")
class Prodigit3311F(RealDriver, ElectronicLoad):
    """Driver for Prodigit 3311F DC Electronic Load (3310F Series plug-in module).

    Validated Model: 3311F (60V, 60A, 300W), hosted in a 3302F mainframe
    chassis. Unlike a standalone electronic load (e.g. `SiglentSDL1000X`),
    the 3311F is a plug-in module: every command is prefixed with the
    chassis slot address (``CHAN<n>``), selected once per session
    (default slot 1, override via ``slot=``). CC/CV/CR/CP command shape
    is otherwise directly comparable to `ItechIT8512Plus`.

    Command Reference (3310F Series Plug-In Electronic Load Module Operation Manual):
        - CHAN<n>                   — select active mainframe slot
        - MODE:CC / MODE:CV / MODE:CR / MODE:CP  — operating mode select
        - MODE?                     — query active mode
        - CURR <a> / CURR?          — CC-mode current setpoint
        - VOLT <v> / VOLT?          — CV-mode voltage setpoint
        - RES <ohm> / RES?          — CR-mode resistance setpoint
        - POW <w> / POW?            — CP-mode power setpoint
        - LOAD ON / LOAD OFF        — input on/off
        - LOAD?                     — query input state
        - MEAS:VOLT? / MEAS:CURR? / MEAS:POW?  — measured actual readings
        - VOLT:PROT <v>             — OVP trip point
        - CURR:PROT <a>             — OCP trip point
        - POW:PROT <w>              — OPP trip point
        - PROT:CLE                  — clear tripped protection
    """

    def __init__(self, resource: str) -> None:
        super().__init__(resource)
        self._slot = 1

    def _select_slot(self, slot: int = None) -> None:
        self.write(f"CHAN{slot if slot else self._slot}")

    def set_mode(self, mode: str, slot: int = None) -> None:
        mode_upper = mode.upper()
        if mode_upper not in ("CC", "CV", "CR", "CP"):
            raise ValueError(f"Invalid mode: {mode}")
        self._select_slot(slot)
        self.safe_send(f"MODE:{mode_upper}")

    def get_mode(self, slot: int = None) -> str:
        self._select_slot(slot)
        return self.query_ascii("MODE?").strip()

    def set_current(self, amps: float, slot: int = None) -> None:
        self._select_slot(slot)
        self.safe_send(f"CURR {amps}")

    def get_current(self, slot: int = None) -> float:
        self._select_slot(slot)
        return float(self.query_ascii("CURR?"))

    def set_voltage(self, volts: float, slot: int = None) -> None:
        self._select_slot(slot)
        self.safe_send(f"VOLT {volts}")

    def get_voltage(self, slot: int = None) -> float:
        self._select_slot(slot)
        return float(self.query_ascii("VOLT?"))

    def set_resistance(self, ohms: float, slot: int = None) -> None:
        self._select_slot(slot)
        self.safe_send(f"RES {ohms}")

    def get_resistance(self, slot: int = None) -> float:
        self._select_slot(slot)
        return float(self.query_ascii("RES?"))

    def set_power(self, watts: float, slot: int = None) -> None:
        self._select_slot(slot)
        self.safe_send(f"POW {watts}")

    def get_power(self, slot: int = None) -> float:
        self._select_slot(slot)
        return float(self.query_ascii("POW?"))

    def set_input(self, state: bool, slot: int = None) -> None:
        self._select_slot(slot)
        self.safe_send(f"LOAD {'ON' if state else 'OFF'}")

    def get_input(self, slot: int = None) -> bool:
        self._select_slot(slot)
        return self.query_ascii("LOAD?").strip() in ("1", "ON")

    def measure_voltage(self, slot: int = None) -> MeasurementResult:
        self._select_slot(slot)
        val = self.query_ascii("MEAS:VOLT?")
        return MeasurementResult(float(val), "V")

    def measure_current(self, slot: int = None) -> MeasurementResult:
        self._select_slot(slot)
        val = self.query_ascii("MEAS:CURR?")
        return MeasurementResult(float(val), "A")

    def measure_power(self, slot: int = None) -> MeasurementResult:
        self._select_slot(slot)
        val = self.query_ascii("MEAS:POW?")
        return MeasurementResult(float(val), "W")

    def set_ovp(self, voltage: float, slot: int = None) -> None:
        self._select_slot(slot)
        self.safe_send(f"VOLT:PROT {voltage}")

    def set_ocp(self, current: float, slot: int = None) -> None:
        self._select_slot(slot)
        self.safe_send(f"CURR:PROT {current}")

    def set_opp(self, power: float, slot: int = None) -> None:
        self._select_slot(slot)
        self.safe_send(f"POW:PROT {power}")

    def clear_protection(self, slot: int = None) -> None:
        self._select_slot(slot)
        self.safe_send("PROT:CLE")

    def shutdown_safety(self) -> None:
        self.set_input(False)
        self.sync_config()
