from .base import PowerMeter
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


class _Boonton4530Base(RealDriver, PowerMeter):
    """Shared driver for the Boonton 4530 Series RF Peak Power Meter.

    Covers both the single-channel Model 4531 and dual-channel Model
    4532; both share the same SCPI 1993 command tree over GPIB or
    RS-232 (no USB/LAN on this generation).

    Command Reference (4530 Series Instruction Manual, Table 4-1):
        - SENSe[n]:CORRection:FREQuency <GHz>   — CW frequency for the
          sensor's cal-factor lookup (manual argument is in GHz)
        - CALCulate[n]:UNITs {DBM|WATTS}        — readout units
        - SENSe[n]:CORRection:OFFset <db>       — relative gain/loss offset
        - MEASure[n]:POWer?                     — CW average power
        - FETCh[n]:ARRay:AMEAsure:POWer?        — pulse-mode automatic
          measurements; first field is the pulse-on peak power
        - FETCh[n]:ARRay:AMEAsure:TIMe?         — pulse timing; third
          field is the pulse width
        - SENSe[n]:BANDwidth {HIGH|LOW}         — sensor video bandwidth
        - TRIGger:SOURce {SENSOR1|SENSOR2|EXTERNAL|IMMEDIATE|BUS}
        - TRIGger:LEVel <dbm>
        - CALibration:INTernal:ZERO             — sensor zero against the
          50 MHz internal calibrator (use EXTernal for the 1 GHz one)
        - *IDN? / *RST / *CLS / *OPC?

    The 4530 defines no ``FREQ``, ``UNIT:POWER``, ``SENS:BAND:VIDEO``,
    ``TRIG:SOURCE INT``, ``MEAS:PEAK?`` or ``MEAS:PULSE:WIDTH?`` command;
    those belong to other power-meter families (e.g. Keysight N191x).
    """

    @staticmethod
    def _chan_cmd(command: str, channel: int) -> str:
        """Return ``command`` with the 1|2 channel suffix after its root.

        ``MEASure:POWer?`` -> ``MEASure2:POWer?``. Channel 1 uses the
        suffix-less default form the manual shows as ``[1|2]``.
        """
        if channel == 1:
            return command
        root, sep, rest = command.partition(":")
        return f"{root}{channel}{sep}{rest}"

    def set_frequency(self, hz: float) -> None:
        self.safe_send(f"SENS:CORR:FREQ {hz / 1e9:.9g} GHz")

    def get_frequency(self) -> float:
        return float(self.query_ascii("SENS:CORR:FREQ?")) * 1e9

    def set_power_unit(self, unit: str) -> None:
        unit_upper = unit.upper()
        if unit_upper not in ("DBM", "W", "WATTS"):
            raise ValueError("unit must be 'DBM' or 'W'")
        self.safe_send(f"CALC:UNIT {'DBM' if unit_upper == 'DBM' else 'WATTS'}")

    def set_offset(self, db: float) -> None:
        self.safe_send(f"SENS:CORR:OFF {db}")

    def get_offset(self) -> float:
        return float(self.query_ascii("SENS:CORR:OFF?"))

    def measure_power(self, channel: int = 1) -> MeasurementResult:
        cmd = self._chan_cmd("MEAS:POW?", channel)
        return MeasurementResult(float(self.query_ascii(cmd)), "dBm", channel=channel)

    def measure_peak_power(self, channel: int = 1) -> MeasurementResult:
        """Pulse-on peak power (pulse mode only).

        The 4530 has no scalar peak query: automatic pulse measurements
        come back as an array from FETCh:ARRay:AMEAsure:POWer?, whose
        first field is ``PulseOnPeak``.
        """
        cmd = self._chan_cmd("FETC:ARR:AMEA:POW?", channel)
        peak = float(self.query_ascii(cmd).split(",")[0])
        return MeasurementResult(peak, "dBm", channel=channel)

    def set_video_bandwidth(self, band: str) -> None:
        """Selects the sensor video bandwidth: 'HIGH' (normal) or 'LOW'.

        The 4530 takes a HIGH/LOW setting, not a numeric bandwidth in Hz.
        """
        band_upper = str(band).upper()
        if band_upper not in ("HIGH", "LOW"):
            raise ValueError(
                "4530 video bandwidth is 'HIGH' or 'LOW', not a frequency in Hz"
            )
        self.safe_send(f"SENS:BAND {band_upper}")

    def get_video_bandwidth(self) -> str:
        return self.query_ascii("SENS:BAND?").strip().upper()

    def set_trigger_source(self, source: str) -> None:
        key = source.upper()
        mapping = {
            "INTERNAL": "SENSOR1", "INT": "SENSOR1", "SENSOR1": "SENSOR1",
            "SENSOR2": "SENSOR2", "EXTERNAL": "EXTERNAL", "EXT": "EXTERNAL",
            "IMMEDIATE": "IMMEDIATE", "FREE_RUN": "IMMEDIATE",
            "FREERUN": "IMMEDIATE", "BUS": "BUS",
        }
        if key not in mapping:
            raise ValueError(f"Invalid trigger source: {source}")
        self.safe_send(f"TRIG:SOUR {mapping[key]}")

    def set_trigger_level(self, dbm: float) -> None:
        self.safe_send(f"TRIG:LEV {dbm}")

    def measure_pulse_width(self, channel: int = 1) -> MeasurementResult:
        """Pulse width in seconds (pulse mode only).

        FETCh:ARRay:AMEAsure:TIMe? returns PulseFreq, PulsePeriod,
        PulseWidth, Offtime, DutyCycle, Risetime, Falltime.
        """
        cmd = self._chan_cmd("FETC:ARR:AMEA:TIM?", channel)
        fields = self.query_ascii(cmd).split(",")
        return MeasurementResult(float(fields[2]), "s", channel=channel)

    def zero(self) -> None:
        """Zeroes the CW sensor against the internal 50 MHz calibrator."""
        self.safe_send("CAL:INT:ZERO")
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

    Channel 2 methods mirror the channel-1 (default) ones with a
    ``channel=2`` argument, which the 4530 spells as a SCPI suffix
    (``MEAS2:POW?``), not as a command parameter.
    """
