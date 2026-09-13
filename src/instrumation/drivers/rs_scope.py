from typing import List
from .base import Oscilloscope
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult

try:
    import numpy as np
except ImportError:
    np = None


@register_driver("SCOPE")
class RohdeSchwarzHMOCompact(RealDriver, Oscilloscope):
    """Driver for Rohde & Schwarz / Hameg HMO Compact Series Oscilloscopes.

    Covers HMO722/724, HMO1022/1024, HMO1522/1524, HMO2022/2024. Edge
    trigger only; math (FFT, add/sub/mul), decode, and mask-test features
    from the Programmer's Manual are not yet implemented.

    SCPI Reference (HMO Compact SCPI Programmer's Manual):
        - CHAN<n>:STAT {ON|OFF}         — channel display on/off
        - CHAN<n>:SCAL <v>              — vertical scale (V/div)
        - CHAN<n>:OFFS <v>              — vertical offset
        - CHAN<n>:COUP {AC|DC|GND}      — input coupling
        - TIM:SCAL <s>                  — horizontal scale (s/div)
        - TIM:OFFS <s>                  — horizontal offset
        - TRIG:A:MODE {AUTO|NORM}       — trigger sweep mode
        - TRIG:A:EDGE:SOUR CH<n>        — edge trigger source
        - TRIG:A:LEV<n> <v>             — trigger level
        - TRIG:A:EDGE:SLOP {POS|NEG}    — trigger slope
        - CHAN<n>:DATA:POIN {DEF|MAX}   — waveform data length mode
        - CHAN<n>:DATA?                 — waveform data (ASCII floats, preceded by header)
        - MEAS<n>:SOUR CH<n>            — assign measurement slot to channel
        - MEAS<n>:MAIN {FREQ|PEAK|PPE|PER}, MEAS<n>:RES? — configure + read a measurement
        - RUN / STOP / SING             — acquisition control
        - AUToscale                     — automatic scale
        - HCOP:DATA? PNG                — screenshot
    """

    def __init__(self, resource: str) -> None:
        super().__init__(resource)
        self.max_voltage = 400.0
        self._channel_count = 4

    def _validate_channel(self, channel: int) -> None:
        if channel < 1 or channel > self._channel_count:
            raise ValueError(f"Channel must be 1..{self._channel_count}, got {channel}")

    def preset(self, automation_optimized: bool = True) -> None:
        self.write("*RST")
        self.wait_ready()

    def run(self) -> None:
        self.write("RUN")

    def stop(self) -> None:
        self.write("STOP")

    def single(self) -> None:
        self.write("SING")

    def auto_scale(self) -> None:
        self.write("AUToscale")
        self.wait_ready()

    # ── Channel Configuration ──────────────────────────────────

    def set_channel_display(self, channel: int, state: bool) -> None:
        self._validate_channel(channel)
        self.safe_send(f"CHAN{channel}:STAT {'ON' if state else 'OFF'}")

    def get_channel_display(self, channel: int) -> bool:
        self._validate_channel(channel)
        resp = self.query(f"CHAN{channel}:STAT?").strip().upper()
        # HMO reports boolean state as ON/OFF (SCPI); fall back to 1/0
        # so drivers mocking/test-harness backends that return numeric
        # booleans keep working.
        if resp in ("ON", "1"):
            return True
        if resp in ("OFF", "0"):
            return False
        raise ValueError(f"Unrecognized CHAN{channel}:STAT? response: {resp!r}")

    def set_channel_scale(self, channel: int, scale: float) -> None:
        self._validate_channel(channel)
        self.safe_send(f"CHAN{channel}:SCAL {scale}")

    def get_channel_scale(self, channel: int) -> float:
        self._validate_channel(channel)
        return float(self.query(f"CHAN{channel}:SCAL?"))

    def set_channel_offset(self, channel: int, offset: float) -> None:
        self._validate_channel(channel)
        self.safe_send(f"CHAN{channel}:OFFS {offset}")

    def get_channel_offset(self, channel: int) -> float:
        self._validate_channel(channel)
        return float(self.query(f"CHAN{channel}:OFFS?"))

    def set_channel_coupling(self, channel: int, coupling: str) -> None:
        self._validate_channel(channel)
        valid = {"AC", "DC", "GND"}
        if coupling.upper() not in valid:
            raise ValueError(f"Invalid coupling: {coupling}")
        self.safe_send(f"CHAN{channel}:COUP {coupling.upper()}")

    def get_channel_coupling(self, channel: int) -> str:
        self._validate_channel(channel)
        return self.query(f"CHAN{channel}:COUP?")

    # ── Timebase ────────────────────────────────────────────────

    def set_timebase_scale(self, scale: float) -> None:
        self.safe_send(f"TIM:SCAL {scale}")

    def get_timebase_scale(self) -> float:
        return float(self.query("TIM:SCAL?"))

    def set_timebase_offset(self, offset: float) -> None:
        self.safe_send(f"TIM:OFFS {offset}")

    def get_timebase_offset(self) -> float:
        return float(self.query("TIM:OFFS?"))

    # ── Trigger (Edge Only) ─────────────────────────────────────

    def set_trigger(self, source: str, level: float, slope: str) -> None:
        """Configure edge trigger.

        Args:
            source: e.g. "CH1", "CH2"
            level: trigger level in volts
            slope: POS or NEG
        """
        valid_slope = {"POS", "NEG"}
        if slope.upper() not in valid_slope:
            raise ValueError(f"Invalid slope: {slope}")
        self.safe_send(f"TRIG:A:EDGE:SOUR {source.upper()}")
        self.safe_send(f"TRIG:A:LEV1 {level}")
        self.safe_send(f"TRIG:A:EDGE:SLOP {slope.upper()}")

    def set_trigger_mode(self, mode: str) -> None:
        """TRIG:A:MODE — AUTO or NORM."""
        valid = {"AUTO", "NORM"}
        if mode.upper() not in valid:
            raise ValueError(f"Invalid trigger mode: {mode}")
        self.safe_send(f"TRIG:A:MODE {mode.upper()}")

    # ── Waveform Readout ────────────────────────────────────────

    def get_waveform(self, channel: int) -> MeasurementResult:
        """Fetch waveform data for a channel as calibrated voltage samples.

        HMO's CHAN<n>:DATA? returns ASCII comma-separated voltage values
        directly (already scaled), unlike Keysight/Rigol's raw-code +
        preamble scheme.
        """
        self._validate_channel(channel)
        self.write(f"CHAN{channel}:DATA:POIN DEF")
        raw = self.query(f"CHAN{channel}:DATA?")
        voltage = [float(v) for v in raw.strip().split(",") if v.strip()]
        if np is not None:
            voltage = np.array(voltage)
        return MeasurementResult(voltage, "V", channel=channel)

    def get_screenshot(self) -> bytes:
        self.write("HCOP:DATA? PNG")
        return self.inst.read_raw()

    # ── Measurements ────────────────────────────────────────────

    def _measure(self, channel: int, main: str, slot: int = 1) -> str:
        self.safe_send(f"MEAS{slot}:SOUR CH{channel}")
        self.safe_send(f"MEAS{slot}:MAIN {main}")
        return self.query_ascii(f"MEAS{slot}:RES?")

    def measure_frequency(self, channel: int = 1) -> MeasurementResult:
        val = self._measure(channel, "FREQ")
        return MeasurementResult(float(val), "Hz", channel=channel)

    def measure_duty_cycle(self, channel: int = 1) -> MeasurementResult:
        val = self._measure(channel, "PDCY")
        return MeasurementResult(float(val), "%", channel=channel)

    def measure_v_peak_to_peak(self, channel: int = 1) -> MeasurementResult:
        val = self._measure(channel, "PEAK")
        return MeasurementResult(float(val), "V", channel=channel)

    def measure_rise_time(self, channel: int = 1) -> MeasurementResult:
        val = self._measure(channel, "RTIM")
        return MeasurementResult(float(val), "s", channel=channel)

    def measure_fall_time(self, channel: int = 1) -> MeasurementResult:
        val = self._measure(channel, "FTIM")
        return MeasurementResult(float(val), "s", channel=channel)

    def measure_period(self, channel: int = 1) -> MeasurementResult:
        val = self._measure(channel, "PER")
        return MeasurementResult(float(val), "s", channel=channel)

    # ── Safety & Shutdown ───────────────────────────────────────

    def shutdown_safety(self) -> None:
        self.stop()
        self.sync_config()
