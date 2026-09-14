from .base import PowerSupply
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("PSU")
class RohdeSchwarzHMP4040(RealDriver, PowerSupply):
    """Driver for Rohde & Schwarz HMP4040 Series Power Supplies.

    Validated Model: HMP4040 (4 independent channels). Also covers the
    HMP2020/HMP2030/HMP4030 siblings, which share the same SCPI dialect
    with fewer channels. Channels are selected via ``INST:NSEL {1..4}``;
    once selected, plain ``VOLT``/``CURR``/``OUTP`` commands address that
    channel -- the same select-then-command shape as `BKPrecision9130B`,
    distinct from the GW Instek GPP's numeric-suffix-on-keyword dialect.

    SCPI Reference (HMP Series SCPI Programmers Manual):
        - INST:NSEL {1|2|3|4}       — select active output channel
        - VOLT {volts} / VOLT?      — set/query voltage on active channel
        - CURR {amps} / CURR?       — set/query current limit on active channel
        - OUTP:SEL {ON|OFF}         — arm/disarm active channel for :OUTP:GEN
        - OUTP:GEN {ON|OFF}         — global output enable (all armed channels)
        - OUTP {ON|OFF} / OUTP?     — output on/off for active channel
        - MEAS:VOLT? / MEAS:CURR?   — measured actual voltage/current
        - VOLT:PROT {volts}         — set OVP trip point
        - CURR:PROT {amps}          — set OCP trip point (fuse-link protection)
        - FUSE:STAT {ON|OFF}        — enable/disable channel fuse coupling
        - *IDN? / *RST / SYST:ERR?
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
        self._select_channel(channel)
        return float(self.query_ascii("VOLT?"))

    def set_current_limit(self, current: float, channel: int = None) -> None:
        self._select_channel(channel)
        self.safe_send(f"CURR {current}")

    def get_current(self, channel: int = None) -> MeasurementResult:
        self._select_channel(channel)
        val = self.query_ascii("CURR?")
        return MeasurementResult(float(val), "A")

    def set_output(self, state: bool, channel: int = None) -> None:
        self._select_channel(channel)
        self.safe_send(f"OUTP {'ON' if state else 'OFF'}")

    def get_output(self, channel: int = None) -> bool:
        self._select_channel(channel)
        return self.query_ascii("OUTP?").strip() in ("1", "ON")

    def set_ovp(self, voltage: float, channel: int = None) -> None:
        self._select_channel(channel)
        self.safe_send(f"VOLT:PROT {voltage}")

    def set_ocp(self, current: float, channel: int = None) -> None:
        self._select_channel(channel)
        self.safe_send(f"CURR:PROT {current}")

    def clear_protection(self, channel: int = None) -> None:
        self._select_channel(channel)
        self.safe_send("FUSE:STAT OFF")

    def measure_voltage_actual(self, channel: int = None) -> MeasurementResult:
        self._select_channel(channel)
        val = self.query_ascii("MEAS:VOLT?")
        return MeasurementResult(float(val), "V")

    def measure_current(self, channel: int = None) -> MeasurementResult:
        self._select_channel(channel)
        val = self.query_ascii("MEAS:CURR?")
        return MeasurementResult(float(val), "A")

    def set_global_output(self, state: bool) -> None:
        """Enables/disables all channels previously armed via OUTP:SEL."""
        self.safe_send(f"OUTP:GEN {'ON' if state else 'OFF'}")

    def shutdown_safety(self) -> None:
        for ch in (1, 2, 3, 4):
            self.set_output(False, channel=ch)
            self.set_voltage(0.0, channel=ch)
        self.set_global_output(False)
        self.sync_config()
