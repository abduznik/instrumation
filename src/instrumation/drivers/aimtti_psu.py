from .base import PowerSupply
from .registry import register_driver
from .real import RealDriver
from ..exceptions import ConfigurationError
from ..results import MeasurementResult


@register_driver("PSU")
class AimTTiCPX400DP(RealDriver, PowerSupply):
    """Driver for AIM-TTi CPX400DP Dual DC Power Supply (PowerFlex series).

    Validated Model: CPX400DP (2 independent 60V/20A channels). Unlike
    the GW Instek/BK Precision/Rigol SCPI-99 PSU dialects already in
    this library, AIM-TTi's CPX series puts the channel number directly
    on the command keyword with no colon (``V1 <v>``, ``I2 <i>``,
    ``OP1 {0|1}``) rather than a ``SOURce<n>:`` prefix or an
    ``INST:NSEL`` select-then-command round-trip.

    Command Reference (CPX400D/DP Instruction Manual, "Remote Commands"):
        - V<n> <volts> / V<n>?      — set/query voltage setpoint, channel n
        - I<n> <amps> / I<n>?       — set/query current limit, channel n
        - OP<n> {0|1} / OP<n>?      — output off/on, channel n
        - V<n>O? / I<n>O?           — measured actual voltage/current, channel n
        - OVP<n> <volts>            — set over-voltage protection trip point
        - OCP<n> <amps>             — set over-current protection trip point
        - OVP<n>? / OCP<n>?         — query the protection trip points
        - TRIPRST                   — clear all trip conditions
        - CONFIG {0|2} / CONFIG?    — 0 = voltage tracking, 2 = independent
        - RATIO <pct>               — slave/main ratio in tracking mode
        - EER?                      — execution error register (0 = no error)
        - *IDN? / *RST / *CLS / *WAI

    The CPX400DP has no SCPI error queue (0 hits for ``SYST:ERR?`` in the
    manual): ``EER?`` reads and clears the Execution Error Register and
    answers a bare error number. It also defines no ``*OPT?`` -- the
    feature set is fixed per model.
    """

    CHANNELS = (1, 2)

    # Non-SCPI error register: bare <nr1>, 0 = no error (see check_errors).
    ERROR_QUERY = "EER?"

    def _discover_options(self) -> None:
        """No *OPT? query on the CPX400DP -- the command list defines none."""
        self.options = []

    def check_errors(self) -> None:
        """Read the Execution Error Register; ``EER?`` answers a bare number."""
        if not self.check_errors_enabled:
            return
        err = self.inst.query(self.ERROR_QUERY).strip()
        if err and err.split()[0] != "0":
            self.error_stack.append(err)
            resource_name = self.identity.get("model") or self.resource
            raise ConfigurationError(f"Hardware Error on {resource_name}: EER {err}")

    def _n(self, channel: int = None) -> int:
        return channel if channel else 1

    def preset(self, automation_optimized: bool = True) -> None:
        self.write("*RST")
        self.sync_config()

    def set_voltage(self, voltage: float, channel: int = None) -> None:
        self.safe_send(f"V{self._n(channel)} {voltage}")

    def get_voltage(self, channel: int = None) -> float:
        resp = self.query_ascii(f"V{self._n(channel)}?")
        return float(resp.split()[-1])

    def set_current_limit(self, current: float, channel: int = None) -> None:
        self.safe_send(f"I{self._n(channel)} {current}")

    def get_current(self, channel: int = None) -> MeasurementResult:
        resp = self.query_ascii(f"I{self._n(channel)}?")
        return MeasurementResult(float(resp.split()[-1]), "A")

    def set_output(self, state: bool, channel: int = None) -> None:
        self.safe_send(f"OP{self._n(channel)} {'1' if state else '0'}")

    def get_output(self, channel: int = None) -> bool:
        return self.query_ascii(f"OP{self._n(channel)}?").strip() in ("1", "ON")

    def set_ovp(self, voltage: float, channel: int = None) -> None:
        self.safe_send(f"OVP{self._n(channel)} {voltage}")

    def set_ocp(self, current: float, channel: int = None) -> None:
        self.safe_send(f"OCP{self._n(channel)} {current}")

    def clear_protection(self, channel: int = None) -> None:
        """Clear all trip conditions (``TRIPRST`` is instrument-wide)."""
        self.safe_send("TRIPRST")

    def measure_voltage_actual(self, channel: int = None) -> MeasurementResult:
        resp = self.query_ascii(f"V{self._n(channel)}O?")
        return MeasurementResult(float(resp.rstrip("V\r\n ")), "V")

    def measure_current(self, channel: int = None) -> MeasurementResult:
        resp = self.query_ascii(f"I{self._n(channel)}O?")
        return MeasurementResult(float(resp.rstrip("A\r\n ")), "A")

    def set_track_mode(self, mode: int) -> None:
        """Set output coupling exactly as ``CONFIG`` defines it.

        0 = voltage tracking (output 2 follows output 1 by ``RATIO``),
        2 = outputs independent. The CPX400DP has no series/parallel
        mode, so any other value is rejected. Outputs are switched off
        first: ``CONFIG`` with output 2 on is execution error 104.
        """
        if mode not in (0, 2):
            raise ValueError("mode must be 0 (voltage tracking) or 2 (independent)")
        for ch in self.CHANNELS:
            self.set_output(False, channel=ch)
        self.safe_send(f"CONFIG {mode}")

    def shutdown_safety(self) -> None:
        for ch in self.CHANNELS:
            self.set_output(False, channel=ch)
            self.set_voltage(0.0, channel=ch)
