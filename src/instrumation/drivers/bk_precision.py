from .base import PowerSupply, ElectronicLoad
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("PSU")
class BKPrecision9130B(RealDriver, PowerSupply):
    """Driver for BK Precision 9130B Series Triple Output DC Power Supplies.

    Three independent channels selected via ``INST:NSEL {1|2|3}``; once
    selected, plain ``VOLT``/``CURR``/``OUTP`` commands address that channel
    (SCPI-99 style). All ``PowerSupply`` interface methods operate on the
    active channel (default 1); pass ``channel=`` to target another output.

    SCPI Reference (9130B Series Programming Manual):
        - INST:NSEL {1|2|3}         — select active output channel
        - VOLT {volts}              — set voltage on active channel
        - VOLT?                     — query voltage setpoint
        - CURR {amps}               — set current limit on active channel
        - CURR?                     — query current limit setpoint
        - MEAS:VOLT?                — measure actual output voltage
        - MEAS:CURR?                — measure actual output current
        - OUTP {ON|OFF}             — output on/off for active channel
        - OUTP?                     — query output state
        - VOLT:PROT {volts}         — set OVP trip point
        - CURR:PROT {amps}          — set OCP trip point
        - OUTP:TRAC {ON|OFF}        — enable/disable tracking mode (CH2/CH3)
        - *SAV {index} / *RCL {index} — memory store/recall (1-9)
    """

    def __init__(self, resource: str) -> None:
        super().__init__(resource)
        self._active_channel = 1

    def _select_channel(self, channel: int = None) -> None:
        ch = channel if channel else self._active_channel
        self.write(f"INST:NSEL {ch}")

    def preset(self, automation_optimized: bool = True) -> None:
        self.write("*RST")
        self.sync_config()

    def set_voltage(self, voltage: float, channel: int = None) -> None:
        self._select_channel(channel)
        self.safe_send(f"VOLT {voltage}")

    def get_voltage(self, channel: int = None) -> float:
        """Returns the programmed voltage setpoint for the given channel."""
        self._select_channel(channel)
        return float(self.query_ascii("VOLT?"))

    def set_current_limit(self, current: float, channel: int = None) -> None:
        self._select_channel(channel)
        self.safe_send(f"CURR {current}")

    def get_current(self, channel: int = None) -> MeasurementResult:
        """Returns the programmed current limit setpoint for the given channel."""
        self._select_channel(channel)
        val = self.query_ascii("CURR?")
        return MeasurementResult(float(val), "A")

    def set_output(self, state: bool, channel: int = None) -> None:
        self._select_channel(channel)
        self.write(f"OUTP {'ON' if state else 'OFF'}")

    def get_output(self, channel: int = None) -> bool:
        self._select_channel(channel)
        state = self.query_ascii("OUTP?")
        return state == "1" or state.upper() == "ON"

    def set_ovp(self, voltage: float, channel: int = None) -> None:
        self._select_channel(channel)
        self.write(f"VOLT:PROT {voltage}")

    def get_ovp(self, channel: int = None) -> float:
        self._select_channel(channel)
        return float(self.query("VOLT:PROT?"))

    def set_ocp(self, current: float, channel: int = None) -> None:
        self._select_channel(channel)
        self.write(f"CURR:PROT {current}")

    def get_ocp(self, channel: int = None) -> float:
        self._select_channel(channel)
        return float(self.query("CURR:PROT?"))

    def clear_protection(self) -> None:
        """Clears hardware protection latches (OVP/OCP) on all channels."""
        self.write("OUTP:PROT:CLE")

    def measure_voltage_actual(self, channel: int = None) -> MeasurementResult:
        """Queries the actual measured output voltage on the given channel."""
        self._select_channel(channel)
        val = self.query_ascii("MEAS:VOLT?")
        return MeasurementResult(float(val), "V")

    def measure_current(self, channel: int = None) -> MeasurementResult:
        """Queries the actual measured output current on the given channel."""
        self._select_channel(channel)
        val = self.query_ascii("MEAS:CURR?")
        return MeasurementResult(float(val), "A")

    def measure_power(self, channel: int = None) -> MeasurementResult:
        """Queries the actual measured output power on the given channel."""
        self._select_channel(channel)
        val = self.query_ascii("MEAS:POW?")
        return MeasurementResult(float(val), "W")

    def set_tracking_mode(self, enable: bool) -> None:
        """Enables or disables tracking mode (CH2/CH3 outputs linked)."""
        self.write(f"OUTP:TRAC {'ON' if enable else 'OFF'}")

    def save_state(self, index: int) -> None:
        """Saves current state to memory (1-9)."""
        if not (1 <= index <= 9):
            raise ValueError("Index must be 1-9")
        self.write(f"*SAV {index}")

    def load_state(self, index: int) -> None:
        """Recalls state from memory (1-9)."""
        if not (1 <= index <= 9):
            raise ValueError("Index must be 1-9")
        self.write(f"*RCL {index}")

    def measure_frequency(self) -> MeasurementResult:
        return MeasurementResult(0.0, "Hz")

    def measure_duty_cycle(self) -> MeasurementResult:
        return MeasurementResult(0.0, "%")

    def measure_v_peak_to_peak(self) -> MeasurementResult:
        return MeasurementResult(0.0, "V")

    def shutdown_safety(self) -> None:
        """Safety first: disable output and zero voltage on all channels."""
        for ch in (1, 2, 3):
            self.set_output(False, channel=ch)
            self.set_voltage(0.0, channel=ch)
        self.sync_config()


@register_driver("LOAD")
@register_driver("ELOAD")
class BKPrecision8600(RealDriver, ElectronicLoad):
    """Driver for BK Precision 8600 Series Programmable DC Electronic Loads.

    Supports Constant Current (CC), Constant Voltage (CV), Constant Power
    (CP) and Constant Resistance (CR) modes, plus OVP/OCP/OPP protection
    and battery test mode.

    SCPI Reference (8600 Series Programming Manual):
        - :SOUR:FUNC {CURR|VOLT|POW|RES}   — operating mode
        - :SOUR:CURR:LEV:IMM {amps}        — CC setpoint
        - :SOUR:VOLT:LEV:IMM {volts}       — CV setpoint
        - :SOUR:RES:LEV:IMM {ohms}         — CR setpoint
        - :SOUR:POW:LEV:IMM {watts}        — CP setpoint
        - :SOUR:INP:STAT {ON|OFF}          — input on/off
        - :MEAS:VOLT?/:MEAS:CURR?/:MEAS:POW? — actual measurements
        - :SOUR:VOLT:PROT/:SOUR:CURR:PROT/:SOUR:POW:PROT — OVP/OCP/OPP
        - :SOUR:PROT:CLE                   — clear tripped protection
        - :SOUR:BATT:MODE {ON|OFF}         — battery test mode
        - :SOUR:BATT:LEV:VOLT {volts}      — battery test cutoff voltage
    """

    def preset(self, automation_optimized: bool = True) -> None:
        self.write("*RST")
        self.wait_ready()

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
        return self.query_ascii(":SOUR:INP:STAT?").strip() == "ON"

    def measure_voltage(self) -> MeasurementResult:
        val = self.query_ascii(":MEAS:VOLT?")
        return MeasurementResult(float(val), "V")

    def measure_current(self) -> MeasurementResult:
        val = self.query_ascii(":MEAS:CURR?")
        return MeasurementResult(float(val), "A")

    def measure_power(self) -> MeasurementResult:
        val = self.query_ascii(":MEAS:POW?")
        return MeasurementResult(float(val), "W")

    def set_ovp(self, voltage: float) -> None:
        self.safe_send(f":SOUR:VOLT:PROT {voltage}")

    def set_ocp(self, current: float) -> None:
        self.safe_send(f":SOUR:CURR:PROT {current}")

    def set_opp(self, power: float) -> None:
        self.safe_send(f":SOUR:POW:PROT {power}")

    def clear_protection(self) -> None:
        self.safe_send(":SOUR:PROT:CLE")

    def set_battery_test_mode(self, enable: bool) -> None:
        """Enables or disables battery discharge test mode."""
        self.safe_send(f":SOUR:BATT:MODE {'ON' if enable else 'OFF'}")

    def set_battery_cutoff_voltage(self, volts: float) -> None:
        """Sets the cutoff voltage for battery discharge test mode."""
        self.safe_send(f":SOUR:BATT:LEV:VOLT {volts}")

    def get_battery_test_capacity(self) -> MeasurementResult:
        """Returns the measured discharge capacity (Ah) from the last/current battery test."""
        val = self.query_ascii(":SOUR:BATT:DCH:CAP?")
        return MeasurementResult(float(val), "Ah")

    def shutdown_safety(self) -> None:
        self.set_input(False)
        self.sync_config()
