from .base import ElectronicLoad
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("LOAD")
@register_driver("ELOAD")
class RigolDL3021(RealDriver, ElectronicLoad):
    """Driver for Rigol DL3000 Series Programmable DC Electronic Loads.

    Validated Model: DL3021. Supports Constant Current (CC), Constant
    Voltage (CV), Constant Resistance (CR) and Constant Power (CP)
    modes via ``[SOURce]:FUNCtion``. Unlike the BK Precision 8600, the
    DL3000 series has no software OVP/OCP/OPP *protection-level*
    subsystem in its base command set (OCP/OPP in the front-panel menu
    are test *modes*, not simple trip-point protection) -- those
    methods log an unsupported-feature warning here.

    SCPI Reference (DL3000 Series Programming Manual):
        - [SOURce]:FUNCtion {CURRent|RESistance|VOLTage|POWer}
        - [SOURce]:FUNCtion:MODE {FIXed|LIST|WAVe|BATTery}
        - [SOURce]:CURRent[:LEVel][:IMMediate] <amps>
        - [SOURce]:VOLTage[:LEVel][:IMMediate] <volts>
        - [SOURce]:RESistance[:LEVel][:IMMediate] <ohms>
        - [SOURce]:POWer[:LEVel][:IMMediate] <watts>
        - [SOURce]:INPut[:STATe] {ON|OFF}
        - [SOURce]:INPut[:STATe]?
        - MEASure:VOLTage[:DC]? / MEASure:CURRent[:DC]? / MEASure:POWer[:DC]?
        - MEASure:RESistance[:DC]?
        - MEASure:CAPability?       — battery-test discharge capacity (Ah)
        - MEASure:WATThours?        — accumulated energy (Wh)
        - MEASure:DISChargingTime?  — elapsed battery-test discharge time (s)

    Unsupported: set_ovp/set_ocp/set_opp (no software trip-point commands), clear_protection.
    """

    def set_mode(self, mode: str) -> None:
        mode_upper = mode.upper()
        if mode_upper not in ["CC", "CV", "CR", "CP"]:
            raise ValueError(f"Invalid mode: {mode}")
        scpi_mode = {"CC": "CURR", "CV": "VOLT", "CR": "RES", "CP": "POW"}[mode_upper]
        self.safe_send(f":SOUR:FUNC {scpi_mode}")

    def get_mode(self) -> str:
        scpi_mode = self.query_ascii(":SOUR:FUNC?").strip()
        return {"CURR": "CC", "VOLT": "CV", "RES": "CR", "POW": "CP"}.get(scpi_mode, scpi_mode)

    def set_current(self, amps: float) -> None:
        self.safe_send(f":SOUR:CURR:LEV:IMM {amps}")

    def get_current(self) -> float:
        return float(self.query_ascii(":SOUR:CURR:LEV:IMM?"))

    def set_voltage(self, volts: float) -> None:
        self.safe_send(f":SOUR:VOLT:LEV:IMM {volts}")

    def get_voltage(self) -> float:
        return float(self.query_ascii(":SOUR:VOLT:LEV:IMM?"))

    def set_resistance(self, ohms: float) -> None:
        self.safe_send(f":SOUR:RES:LEV:IMM {ohms}")

    def get_resistance(self) -> float:
        return float(self.query_ascii(":SOUR:RES:LEV:IMM?"))

    def set_power(self, watts: float) -> None:
        self.safe_send(f":SOUR:POW:LEV:IMM {watts}")

    def get_power(self) -> float:
        return float(self.query_ascii(":SOUR:POW:LEV:IMM?"))

    def set_input(self, state: bool) -> None:
        self.safe_send(f":SOUR:INP:STAT {'ON' if state else 'OFF'}")

    def get_input(self) -> bool:
        return self.query_ascii(":SOUR:INP:STAT?").strip() in ("1", "ON")

    def measure_voltage(self) -> MeasurementResult:
        return self._meas(":MEAS:VOLT?", "V")

    def measure_current(self) -> MeasurementResult:
        return self._meas(":MEAS:CURR?", "A")

    def measure_power(self) -> MeasurementResult:
        return self._meas(":MEAS:POW?", "W")

    def measure_resistance(self) -> MeasurementResult:
        return self._meas(":MEAS:RES?", "Ohm")

    def set_battery_test_mode(self, enable: bool) -> None:
        """Switches the source function mode to/from BATTery discharge testing."""
        self.safe_send(f":SOUR:FUNC:MODE {'BATT' if enable else 'FIX'}")

    def get_battery_test_capacity(self) -> MeasurementResult:
        """Returns the measured discharge capacity (Ah) from the current battery test."""
        return self._meas(":MEAS:CAP?", "Ah")

    def get_watt_hours(self) -> MeasurementResult:
        """Returns accumulated energy consumed (Wh)."""
        return self._meas(":MEAS:WATT?", "Wh")

    def get_discharging_time(self) -> MeasurementResult:
        """Returns elapsed discharge time (s) during a battery test."""
        return self._meas(":MEAS:DISC?", "s")

    def shutdown_safety(self) -> None:
        self.set_input(False)
        self.sync_config()
