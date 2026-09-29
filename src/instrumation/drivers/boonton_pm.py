from .base import PowerMeter
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


class _Boonton4530Base(RealDriver, PowerMeter):
    """Shared driver for the Boonton 4530 Series RF Peak Power Meter.

    Covers both the single-channel Model 4531 and dual-channel Model
    4532; both share the same SCPI 1993 command tree over GPIB or
    RS-232 (no USB/LAN on this generation).

    Command Reference (4530 Series Instruction Manual):
        - FREQ <hz> / FREQ?              — CW frequency for cal-factor lookup
        - UNIT:POWER {DBM|W} / UNIT:POWER?  — readout unit
        - CAL1:OFFSET <db> / CAL1:OFFSET?   — relative gain/loss offset
        - MEAS:POWER? / FETCH:POWER?     — CW average power reading
        - MEAS:PEAK? / FETCH:PEAK?       — peak (pulse) power reading
        - SENS:BAND:VIDEO <hz>           — video bandwidth for pulse demod
        - TRIG:SOURCE {INT|EXT|FREERUN}  — trigger source select
        - TRIG:LEVEL <dbm>               — trigger level for peak capture
        - MEAS:PULSE:WIDTH?              — measured pulse width
        - CAL:ZERO                       — sensor zero calibration
        - *IDN? / *RST / *CLS / *OPC?
    """

    def set_frequency(self, hz: float) -> None:
        self.safe_send(f"FREQ {hz}")

    def get_frequency(self) -> float:
        return float(self.query_ascii("FREQ?"))

    def set_power_unit(self, unit: str) -> None:
        unit_upper = unit.upper()
        if unit_upper not in ("DBM", "W"):
            raise ValueError("unit must be 'DBM' or 'W'")
        self.safe_send(f"UNIT:POWER {unit_upper}")

    def set_offset(self, db: float) -> None:
        self.safe_send(f"CAL1:OFFSET {db}")

    def get_offset(self) -> float:
        return float(self.query_ascii("CAL1:OFFSET?"))

    def measure_power(self) -> MeasurementResult:
        return self._meas("MEAS:POWER?", "dBm")

    def measure_peak_power(self) -> MeasurementResult:
        return self._meas("MEAS:PEAK?", "dBm")

    def set_video_bandwidth(self, hz: float) -> None:
        self.safe_send(f"SENS:BAND:VIDEO {hz}")

    def get_video_bandwidth(self) -> float:
        return float(self.query_ascii("SENS:BAND:VIDEO?"))

    def set_trigger_source(self, source: str) -> None:
        key = source.upper()
        mapping = {"INTERNAL": "INT", "EXTERNAL": "EXT", "FREE_RUN": "FREERUN", "FREERUN": "FREERUN"}
        if key not in mapping and key not in ("INT", "EXT"):
            raise ValueError(f"Invalid trigger source: {source}")
        self.safe_send(f"TRIG:SOURCE {mapping.get(key, key)}")

    def set_trigger_level(self, dbm: float) -> None:
        self.safe_send(f"TRIG:LEVEL {dbm}")

    def measure_pulse_width(self) -> MeasurementResult:
        return self._meas("MEAS:PULSE:WIDTH?", "s")

    def zero(self) -> None:
        self.write("CAL:ZERO")
        self.wait_ready()

    def shutdown_safety(self) -> None:
        self.sync_config()


@register_driver("PEAKPM")
class Boonton4531(_Boonton4530Base):
    """Driver for the Boonton 4531 single-channel RF Peak Power Meter."""
    pass


@register_driver("PEAKPM")
class Boonton4532(_Boonton4530Base):
    """Driver for the Boonton 4532 dual-channel RF Peak Power Meter.

    Adds a second measurement channel; channel 2 methods mirror the
    channel-1 (default) methods with a ``channel=2`` argument.
    """

    def measure_power(self, channel: int = 1) -> MeasurementResult:
        val = self.query_ascii(f"MEAS:POWER? {channel}" if channel != 1 else "MEAS:POWER?")
        return MeasurementResult(float(val), "dBm", channel=channel)

    def measure_peak_power(self, channel: int = 1) -> MeasurementResult:
        val = self.query_ascii(f"MEAS:PEAK? {channel}" if channel != 1 else "MEAS:PEAK?")
        return MeasurementResult(float(val), "dBm", channel=channel)
