from .base import PowerSupply, ElectronicLoad
from .registry import register_driver
from .real import RealDriver, SaveRecallSlots
from ..results import MeasurementResult


@register_driver("PSU")
class BKPrecision9130B(SaveRecallSlots, RealDriver, PowerSupply):
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

    STATE_SLOTS = range(1, 10)
    CHANNELS = (1, 2, 3)

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

    def shutdown_safety(self) -> None:
        """Safety first: disable output and zero voltage on all channels."""
        for ch in self.CHANNELS:
            self.set_output(False, channel=ch)
            self.set_voltage(0.0, channel=ch)
        self.sync_config()


@register_driver("LOAD")
@register_driver("ELOAD")
class BKPrecision8600(RealDriver, ElectronicLoad):
    """Driver for BK Precision 8600 Series Programmable DC Electronic Loads.

    Supports Constant Current (CC), Constant Voltage (CV), Constant Power
    (CP) and Constant Resistance (CR) modes, plus software OCP/OPP protection
    levels.

    SCPI Reference (8600 Series Programming Manual, SCPI 1995.0):
        - [SOURce:]FUNCtion {VOLTage|CURRent|RESistance|POWer}  — operating mode
        - [SOURce:]CURRent[:LEVel][:IMMediate] {amps}          — CC setpoint
        - [SOURce:]VOLTage[:LEVel][:IMMediate] {volts}         — CV setpoint
        - [SOURce:]RESistance[:LEVel][:IMMediate] {ohms}       — CR setpoint
        - [SOURce:]POWer[:LEVel][:IMMediate] {watts}           — CP setpoint
        - [SOURce:]INPut[:STATe] {ON|OFF}                      — input on/off
        - MEASure:VOLTage[:DC]? / MEASure:CURRent[:DC]?        — one-shot readings
        - FETCh:POWer[:DC]?                                    — computed power
        - [SOURce:]CURRent:PROTection:LEVel / :STATe {ON|OFF}  — OCP level + arm
        - [SOURce:]POWer:PROTection[:LEVel]                    — OPP level
        - [SOURce:]PROTection:CLEar                            — clear tripped protection

    Not remote-controllable on this instrument:
        - OVP is a fixed hardware threshold at ~110% of the maximum rated
          voltage (User Manual p.42) — the manual defines no
          ``VOLTage:PROTection`` node, so ``set_ovp`` only logs.
        - The battery test function is front-panel only: "batt" has 0 hits in
          the 100-page programming manual and User Manual p.60 configures and
          runs the test from the front panel.
        - No ``*OPT?`` (0 hits for OPT in the programming manual), so option
          discovery is a no-op instead of queueing -113.
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
        return self.query_ascii(":SOUR:INP:STAT?").strip().upper() in ("1", "ON")

    def measure_voltage(self) -> MeasurementResult:
        return self._meas(":MEAS:VOLT?", "V")

    def measure_current(self) -> MeasurementResult:
        return self._meas(":MEAS:CURR?", "A")

    def measure_power(self) -> MeasurementResult:
        """Computed power — the 8600 only defines ``FETCh:POWer[:DC]?``.

        MEASure has VOLTage and CURRent leaves only (programming manual p.65);
        power is derived from the last acquired sample, so FETCh is the
        documented query.
        """
        return self._meas(":FETCH:POW?", "W")

    def set_ovp(self, voltage: float) -> None:
        """No-op: the 8600's OVP threshold is fixed in hardware.

        The SOURce subsystem defines CURRent:PROTection and POWer:PROTection
        only — ``VOLTage:PROTection`` has 0 hits in the 100-page manual — and
        User Manual p.42 states the OVP limit is ~110% of the maximum rated
        voltage. Clear a trip with ``clear_protection()``.
        """
        self._unsupported_feature(
            "set_ovp (8600 OVP is a fixed hardware threshold at ~110% of "
            "rated voltage; the manual defines no VOLTage:PROTection node)"
        )

    def set_ocp(self, current: float) -> None:
        """Sets the soft OCP level and arms it.

        ``CURRent:PROTection:LEVel`` only stores the trip point; the feature
        itself is off after ``*RST`` (``CURRent:PROTection:STATe`` *RST value
        is OFF, p.48), so sending the level alone never trips.
        """
        self.safe_send(f":SOUR:CURR:PROT:LEV {current}")
        self.safe_send(":SOUR:CURR:PROT:STAT ON")

    def set_opp(self, power: float) -> None:
        self.safe_send(f":SOUR:POW:PROT {power}")

    def clear_protection(self) -> None:
        self.safe_send(":SOUR:PROT:CLE")

    def _discover_options(self) -> None:
        """No *OPT? query on the 8600 — 0 hits for OPT in the manual.

        Sending it would queue -113 "Undefined header", which the next
        error-checked command would then surface as a hardware error.
        """
        self.options = []

    def set_battery_test_mode(self, enable: bool) -> None:
        """No-op: the battery test is front-panel only on the 8600.

        The programming manual has no BATTery subsystem at all ("batt": 0
        hits in 100 pages); User Manual p.60 sets up and runs the test from
        the front panel.
        """
        self._unsupported_feature(
            "set_battery_test_mode (battery test is front-panel only; the "
            "programming manual defines no BATTery subsystem)"
        )

    def set_battery_cutoff_voltage(self, volts: float) -> None:
        """No-op: the battery test is front-panel only (see above)."""
        self._unsupported_feature(
            "set_battery_cutoff_voltage (battery test is front-panel only)"
        )

    def get_battery_test_capacity(self) -> MeasurementResult:
        """No-op: the battery test is front-panel only (see above)."""
        self._unsupported_feature(
            "get_battery_test_capacity (battery test is front-panel only)"
        )
        return MeasurementResult(0.0, "Ah")

    def shutdown_safety(self) -> None:
        self.set_input(False)
        self.sync_config()
