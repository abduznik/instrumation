from .base import ElectronicLoad
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("LOAD")
@register_driver("ELOAD")
class ItechIT8512Plus(RealDriver, ElectronicLoad):
    """Driver for ITECH IT8500+ Series Programmable DC Electronic Loads.

    Validated Model: IT8512+. Supports CC/CV/CR/CP modes via
    ``[SOURce:]FUNCtion``. The IT8500+ series has ``CURRent:PROTection``
    and ``POWer:PROTection`` (OCP/OPP) but no dedicated software OVP
    trip-point command in its base command set -- ``set_ovp`` logs an
    unsupported-feature warning here.

    SCPI Reference (IT8500+ Series Programming Guide):
        - [SOURce:]FUNCtion {CURRent|VOLTage|POWer|RESistance}
        - [SOURce:]CURRent[:LEVel][:IMMediate][:AMPLitude] <amps>
        - [SOURce:]VOLTage[:LEVel][:IMMediate][:AMPLitude] <volts>
        - [SOURce:]RESistance[:LEVel][:IMMediate][:AMPLitude] <ohms>
        - [SOURce:]POWer[:LEVel][:IMMediate][:AMPLitude] <watts>
        - [SOURce:]INPut {ON|OFF} / [SOURce:]INPut?
        - [SOURce:]INPut:SHORt {ON|OFF}    — simulated short-circuit
        - [SOURce:]CURRent:PROTection[:LEVel] <amps>
        - [SOURce:]POWer:PROTection[:LEVel] <watts>
        - MEASure[:SCALar]:VOLTage[:DC]? / :CURRent[:DC]? / :POWer[:DC]?
        - MEASure[:SCALar]:RESistance[:DC]?

    Unsupported: set_ovp (no software OVP trip-point command), clear_protection.
    """

    def set_mode(self, mode: str) -> None:
        mode_upper = mode.upper()
        if mode_upper not in ["CC", "CV", "CR", "CP"]:
            raise ValueError(f"Invalid mode: {mode}")
        scpi_mode = {"CC": "CURR", "CV": "VOLT", "CR": "RES", "CP": "POW"}[mode_upper]
        self.safe_send(f"FUNC {scpi_mode}")

    def get_mode(self) -> str:
        scpi_mode = self.query_ascii("FUNC?").strip()
        return {"CURR": "CC", "VOLT": "CV", "RES": "CR", "POW": "CP"}.get(scpi_mode, scpi_mode)

    def set_current(self, amps: float) -> None:
        self.safe_send(f"CURR:LEV:IMM {amps}")

    def get_current(self) -> float:
        return float(self.query_ascii("CURR:LEV:IMM?"))

    def set_voltage(self, volts: float) -> None:
        self.safe_send(f"VOLT:LEV:IMM {volts}")

    def get_voltage(self) -> float:
        return float(self.query_ascii("VOLT:LEV:IMM?"))

    def set_resistance(self, ohms: float) -> None:
        self.safe_send(f"RES:LEV:IMM {ohms}")

    def get_resistance(self) -> float:
        return float(self.query_ascii("RES:LEV:IMM?"))

    def set_power(self, watts: float) -> None:
        self.safe_send(f"POW:LEV:IMM {watts}")

    def get_power(self) -> float:
        return float(self.query_ascii("POW:LEV:IMM?"))

    def set_input(self, state: bool) -> None:
        self.safe_send(f"INP {'ON' if state else 'OFF'}")

    def get_input(self) -> bool:
        return self.query_ascii("INP?").strip() in ("1", "ON")

    def set_short_circuit(self, state: bool) -> None:
        """Enables/disables the simulated short-circuit input state."""
        self.safe_send(f"INP:SHOR {'ON' if state else 'OFF'}")

    def measure_voltage(self) -> MeasurementResult:
        return self._meas("MEAS:VOLT?", "V")

    def measure_current(self) -> MeasurementResult:
        return self._meas("MEAS:CURR?", "A")

    def measure_power(self) -> MeasurementResult:
        return self._meas("MEAS:POW?", "W")

    def measure_resistance(self) -> MeasurementResult:
        return self._meas("MEAS:RES?", "Ohm")

    def set_ocp(self, current: float) -> None:
        self.safe_send(f"CURR:PROT:LEV {current}")

    def set_opp(self, power: float) -> None:
        self.safe_send(f"POW:PROT:LEV {power}")

    def shutdown_safety(self) -> None:
        self.set_input(False)
        self.sync_config()
