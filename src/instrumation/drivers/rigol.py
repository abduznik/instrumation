from typing import List, Tuple
from .base import SpectrumAnalyzer, Oscilloscope
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult

try:
    import numpy as np
except ImportError:
    np = None

@register_driver("SA")
class RigolDSA(RealDriver, SpectrumAnalyzer):
    """Driver for Rigol DSA Series Spectrum Analyzers."""

    def preset(self, automation_optimized: bool = True) -> None:
        self.write("*RST")
        self.wait_ready()

    def peak_search(self) -> None:
        self.safe_send(":CALC:MARK:MAX")

    def get_marker_amplitude(self) -> MeasurementResult:
        val = self.query_ascii(":CALC:MARK:Y?")
        return MeasurementResult(float(val), "dBm")

    def set_center_freq(self, hz: float) -> None:
        self.safe_send(f":SENS:FREQ:CENT {self.format_frequency(hz)}")

    def get_center_freq(self) -> float:
        return float(self.query(":SENS:FREQ:CENT?"))

    def set_span(self, hz: float) -> None:
        self.safe_send(f":SENS:FREQ:SPAN {hz}")

    def get_span(self) -> float:
        return float(self.query(":SENS:FREQ:SPAN?"))

    def set_rbw(self, hz: float) -> None:
        self.safe_send(f":SENS:BAND:RES {hz}")

    def set_vbw(self, hz: float) -> None:
        self.safe_send(f":SENS:BAND:VID {hz}")

    def set_ref_level(self, dbm: float) -> None:
        self.write(f":DISP:WIND:TRAC:Y:RLEV {dbm}")

    def set_attenuation(self, db: float) -> None:
        self.write(f":SENS:POW:ATT {db}")

    def get_trace_data(self) -> MeasurementResult:
        data = self.query_ascii_values(":TRAC:DATA? TRACE1")
        return MeasurementResult(list(data), "dBm")

    def measure_frequency(self) -> MeasurementResult:
        return MeasurementResult(0.0, "Hz")

    def measure_duty_cycle(self) -> MeasurementResult:
        return MeasurementResult(0.0, "%")

    def measure_v_peak_to_peak(self) -> MeasurementResult:
        return MeasurementResult(0.0, "V")

    def shutdown_safety(self) -> None:
        self.sync_config()


@register_driver("SCOPE")
class RigolDS1054Z(RealDriver, Oscilloscope):
    """Driver for Rigol DS1054Z Digital Oscilloscope.

    Supports the MSO1000Z/DS1000Z Series (DS1054Z, DS1104Z, MSO1054Z, etc.).
    Implements edge trigger only; LA, :SOURce, :DECoder, :MASK, :FUNCtion
    commands are excluded (option-gated or -S variant features).
    """

    def __init__(self, resource: str, rm=None) -> None:
        super().__init__(resource, rm)
        self.max_voltage = 40.0
        self._channel_count = 4

    def connect(self) -> None:
        super().connect()
        self.inst.timeout = 10000
        self.write("*CLS")
        self.write("*WAI")

    # ── IEEE-488.2 Common Commands ─────────────────────────────

    def preset(self, automation_optimized: bool = True) -> None:
        """*RST — Factory default reset."""
        self.write("*RST")
        self.wait_ready()

    def clear_status(self) -> None:
        """*CLS — Clear status registers."""
        self.write("*CLS")

    def sync_config(self) -> None:
        """*CLS + *WAI — Synchronize."""
        self.write("*CLS")
        self.write("*WAI")

    def get_id(self) -> str:
        """*IDN? — Query instrument identification."""
        return self.query("*IDN?")

    # ── Basic Control ──────────────────────────────────────────

    def auto_scale(self) -> None:
        """:AUToscale — Automatically adjust scale for all channels."""
        self.write(":AUToscale")
        self.wait_ready()

    def clear_waveform(self) -> None:
        """:CLEar — Clear waveform data."""
        self.write(":CLEar")

    def run(self) -> None:
        """:RUN — Start acquisition."""
        self.write(":RUN")

    def stop(self) -> None:
        """:STOP — Stop acquisition."""
        self.write(":STOP")

    def single(self) -> None:
        """:SINGle — Single-shot acquisition."""
        self.write(":SINGle")

    def force_trigger(self) -> None:
        """:TFORce — Force a trigger event."""
        self.write(":TFORce")

    # ── Acquisition Configuration ──────────────────────────────

    def set_acquire_type(self, acquire_type: str) -> None:
        """:ACQuire:TYPE — Set acquisition mode.

        Args:
            acquire_type: NORMal, AVERages, PEAK, or HRESolution.
        """
        valid = {"NORMAL", "AVERAGES", "PEAK", "HRESOLUTION"}
        if acquire_type.upper() not in valid:
            raise ValueError(f"Invalid acquire type: {acquire_type}")
        self.safe_send(f":ACQuire:TYPE {acquire_type}")

    def get_acquire_type(self) -> str:
        """:ACQuire:TYPE? — Query acquisition mode."""
        return self.query(":ACQuire:TYPE?")

    def set_acquire_averages(self, count: int) -> None:
        """:ACQuire:AVERages — Set averaging count (2^n, n=1..10).

        Args:
            count: Must be a power of 2 between 2 and 1024.
        """
        if count < 2 or count > 1024:
            raise ValueError(f"Average count must be 2^n (2..1024), got {count}")
        if count & (count - 1) != 0:
            raise ValueError(f"Average count must be a power of 2, got {count}")
        self.safe_send(f":ACQuire:AVERages {count}")

    def set_acquire_memory_depth(self, mdep: int) -> None:
        """:ACQuire:MDEPth — Set memory depth.

        Args:
            mdep: Memory depth in points (14k, 140k, or 14M for DS1054Z).
        """
        self.safe_send(f":ACQuire:MDEPth {mdep}")

    def get_sample_rate(self) -> float:
        """:ACQuire:SRATe? — Query current sample rate (samples/sec)."""
        return float(self.query(":ACQuire:SRATe?"))

    # ── Channel Configuration (per channel n=1..4) ─────────────

    def _validate_channel(self, channel: int) -> None:
        if channel < 1 or channel > self._channel_count:
            raise ValueError(f"Channel must be 1..{self._channel_count}, got {channel}")

    def set_channel_display(self, channel: int, state: bool) -> None:
        """:CHANnel<n>:DISPlay — Enable/disable channel display.

        Args:
            channel: 1-4
            state: True=ON, False=OFF
        """
        self._validate_channel(channel)
        self.safe_send(f":CHANnel{channel}:DISPlay {'ON' if state else 'OFF'}")

    def get_channel_display(self, channel: int) -> bool:
        """:CHANnel<n>:DISPlay? — Query channel display state."""
        self._validate_channel(channel)
        return self.query(f":CHANnel{channel}:DISPlay?") == "1"

    def set_channel_coupling(self, channel: int, coupling: str) -> None:
        """:CHANnel<n>:COUPling — Set input coupling.

        Args:
            channel: 1-4
            coupling: AC, DC, or GND
        """
        self._validate_channel(channel)
        valid = {"AC", "DC", "GND"}
        if coupling.upper() not in valid:
            raise ValueError(f"Invalid coupling: {coupling}")
        self.safe_send(f":CHANnel{channel}:COUPling {coupling.upper()}")

    def get_channel_coupling(self, channel: int) -> str:
        """:CHANnel<n>:COUPling? — Query input coupling."""
        self._validate_channel(channel)
        return self.query(f":CHANnel{channel}:COUPling?")

    def set_channel_scale(self, channel: int, scale: float) -> None:
        """:CHANnel<n>:SCALe — Set vertical scale (volts/div).

        Args:
            channel: 1-4
            scale: Volts per division (e.g. 0.01 to 10.0)
        """
        self._validate_channel(channel)
        self.safe_send(f":CHANnel{channel}:SCALe {scale}")

    def get_channel_scale(self, channel: int) -> float:
        """:CHANnel<n>:SCALe? — Query vertical scale."""
        self._validate_channel(channel)
        return float(self.query(f":CHANnel{channel}:SCALe?"))

    def set_channel_offset(self, channel: int, offset: float) -> None:
        """:CHANnel<n>:OFFSet — Set vertical offset (volts).

        Args:
            channel: 1-4
            offset: DC offset voltage
        """
        self._validate_channel(channel)
        self.safe_send(f":CHANnel{channel}:OFFSet {offset}")

    def get_channel_offset(self, channel: int) -> float:
        """:CHANnel<n>:OFFSet? — Query vertical offset."""
        self._validate_channel(channel)
        return float(self.query(f":CHANnel{channel}:OFFSet?"))

    def set_channel_probe(self, channel: int, attenuation: float) -> None:
        """:CHANnel<n>:PROBe — Set probe attenuation factor.

        Args:
            channel: 1-4
            attenuation: Probe ratio (e.g. 1.0, 10.0)
        """
        self._validate_channel(channel)
        self.safe_send(f":CHANnel{channel}:PROBe {attenuation}")

    def get_channel_probe(self, channel: int) -> float:
        """:CHANnel<n>:PROBe? — Query probe attenuation."""
        self._validate_channel(channel)
        return float(self.query(f":CHANnel{channel}:PROBe?"))

    def set_channel_bw_limit(self, channel: int, bw: str) -> None:
        """:CHANnel<n>:BWLimit — Set bandwidth limit.

        Args:
            channel: 1-4
            bw: 20M (20 MHz) or OFF
        """
        self._validate_channel(channel)
        valid = {"20M", "OFF"}
        if bw.upper() not in valid:
            raise ValueError(f"Invalid bandwidth limit: {bw}")
        self.safe_send(f":CHANnel{channel}:BWLimit {bw.upper()}")

    def get_channel_bw_limit(self, channel: int) -> str:
        """:CHANnel<n>:BWLimit? — Query bandwidth limit."""
        self._validate_channel(channel)
        return self.query(f":CHANnel{channel}:BWLimit?")

    def set_channel_invert(self, channel: int, state: bool) -> None:
        """:CHANnel<n>:INVert — Enable/disable channel inversion.

        Args:
            channel: 1-4
            state: True=ON, False=OFF
        """
        self._validate_channel(channel)
        self.safe_send(f":CHANnel{channel}:INVert {'ON' if state else 'OFF'}")

    def get_channel_invert(self, channel: int) -> bool:
        """:CHANnel<n>:INVert? — Query channel inversion state."""
        self._validate_channel(channel)
        return self.query(f":CHANnel{channel}:INVert?") == "1"

    def set_channel_units(self, channel: int, units: str) -> None:
        """:CHANnel<n>:UNITs — Set channel display units.

        Args:
            channel: 1-4
            units: VOLTage, WATT, AMPere, or UNKNown
        """
        self._validate_channel(channel)
        valid = {"VOLTAGE", "WATT", "AMPERE", "UNKNOWN"}
        if units.upper() not in valid:
            raise ValueError(f"Invalid units: {units}")
        self.safe_send(f":CHANnel{channel}:UNITs {units.upper()}")

    # ── Timebase Configuration ─────────────────────────────────

    def get_timebase_mode(self) -> str:
        """:TIMebase:MODE — Query timebase mode (MAIN, XY, ROLL)."""
        return self.query(":TIMebase:MODE?")

    def set_timebase_scale(self, scale: float) -> None:
        """:TIMebase[:MAIN]:SCALe — Set horizontal scale (seconds/div).

        Args:
            scale: Seconds per division (e.g. 1e-9 to 50.0)
        """
        self.safe_send(f":TIMebase:SCALe {scale}")

    def get_timebase_scale(self) -> float:
        """:TIMebase[:MAIN]:SCALe? — Query horizontal scale."""
        return float(self.query(":TIMebase:SCALe?"))

    def set_timebase_offset(self, offset: float) -> None:
        """:TIMebase[:MAIN]:OFFSet — Set horizontal offset (seconds).

        Args:
            offset: Time offset from trigger point
        """
        self.safe_send(f":TIMebase:OFFSet {offset}")

    def get_timebase_offset(self) -> float:
        """:TIMebase[:MAIN]:OFFSet? — Query horizontal offset."""
        return float(self.query(":TIMebase:OFFSet?"))

    # ── Trigger Configuration (Edge Only) ──────────────────────

    def get_trigger_mode(self) -> str:
        """:TRIGger:MODE — Query trigger mode (EDGE, PULSE, etc.)."""
        return self.query(":TRIGger:MODE?")

    def set_edge_trigger_source(self, source: str) -> None:
        """:TRIGger:EDGe:SOURce — Set edge trigger source.

        Args:
            source: CHANnel1, CHANnel2, CHANnel3, CHANnel4, EXT, or DEMath
        """
        self.safe_send(f":TRIGger:EDGe:SOURce {source}")

    def get_edge_trigger_source(self) -> str:
        """:TRIGger:EDGe:SOURce? — Query edge trigger source."""
        return self.query(":TRIGger:EDGe:SOURce?")

    def set_edge_trigger_slope(self, slope: str) -> None:
        """:TRIGger:EDGe:SLOPe — Set edge trigger slope.

        Args:
            slope: POSitive, NEGative, or RFALl
        """
        valid = {"POSITIVE", "NEGATIVE", "RFALL"}
        if slope.upper() not in valid:
            raise ValueError(f"Invalid slope: {slope}")
        self.safe_send(f":TRIGger:EDGe:SLOPe {slope}")

    def get_edge_trigger_slope(self) -> str:
        """:TRIGger:EDGe:SLOPe? — Query edge trigger slope."""
        return self.query(":TRIGger:EDGe:SLOPe?")

    def set_edge_trigger_level(self, level: float) -> None:
        """:TRIGger:EDGe:LEVel — Set trigger level voltage."""
        self.safe_send(f":TRIGger:EDGe:LEVel {level}")

    def get_edge_trigger_level(self) -> float:
        """:TRIGger:EDGe:LEVel? — Query trigger level voltage."""
        return float(self.query(":TRIGger:EDGe:LEVel?"))

    def set_trigger_sweep(self, sweep: str) -> None:
        """:TRIGger:SWEep — Set trigger sweep mode.

        Args:
            sweep: AUTO, NORMal, or SINGle
        """
        valid = {"AUTO", "NORMAL", "SINGLE"}
        if sweep.upper() not in valid:
            raise ValueError(f"Invalid sweep mode: {sweep}")
        self.safe_send(f":TRIGger:SWEep {sweep.upper()}")

    def get_trigger_sweep(self) -> str:
        """:TRIGger:SWEep? — Query trigger sweep mode."""
        return self.query(":TRIGger:SWEep?")

    def get_trigger_status(self) -> str:
        """:TRIGger:STATus? — Query trigger status.

        Returns: TD (triggered), WAIT, AUTO, STOP, T'D, etc.
        """
        return self.query(":TRIGger:STATus?")

    def set_trigger(self, source: str, level: float, slope: str) -> None:
        """Configure edge trigger (Oscilloscope interface convenience method).

        Args:
            source: CHANnel1, CHANnel2, etc.
            level: Trigger level in volts
            slope: POSITIVE, NEGATIVE, or RFALL
        """
        self.safe_send(":TRIGger:MODE EDGE")
        self.set_edge_trigger_source(source)
        self.set_edge_trigger_level(level)
        self.set_edge_trigger_slope(slope)

    # ── Waveform Readout ───────────────────────────────────────

    def set_waveform_source(self, channel: int) -> None:
        """:WAVeform:SOURce — Select waveform data source.

        Args:
            channel: 1-4 (maps to CHANnel1..CHANnel4)
        """
        self._validate_channel(channel)
        self.safe_send(f":WAVeform:SOURce CHANnel{channel}")

    def get_waveform_source(self) -> str:
        """:WAVeform:SOURce? — Query waveform data source."""
        return self.query(":WAVeform:SOURce?")

    def set_waveform_mode(self, mode: str) -> None:
        """:WAVeform:MODE — Set waveform readout mode.

        Args:
            mode: NORMal, MAXimum, or RAW
        """
        valid = {"NORMAL", "MAXIMUM", "RAW"}
        if mode.upper() not in valid:
            raise ValueError(f"Invalid waveform mode: {mode}")
        self.safe_send(f":WAVeform:MODE {mode.upper()}")

    def set_waveform_format(self, fmt: str) -> None:
        """:WAVeform:FORMat — Set waveform data format.

        Args:
            fmt: WORD, BYTE, or ASCii
        """
        valid = {"WORD", "BYTE", "ASCII"}
        if fmt.upper() not in valid:
            raise ValueError(f"Invalid waveform format: {fmt}")
        self.safe_send(f":WAVeform:FORMat {fmt.upper()}")

    def get_waveform_preamble(self) -> dict:
        """:WAVeform:PREamble? — Query and parse the waveform preamble.

        Returns a dict with keys: format, type, points, count,
        x_increment, x_origin, x_reference, y_increment, y_origin, y_reference.
        """
        resp = self.query(":WAVeform:PREamble?")
        parts = resp.split(",")
        if len(parts) < 10:
            raise ValueError(f"Unexpected preamble format: {resp}")
        return {
            "format": int(parts[0]),
            "type": int(parts[1]),
            "points": int(parts[2]),
            "count": int(parts[3]),
            "x_increment": float(parts[4]),
            "x_origin": float(parts[5]),
            "x_reference": int(parts[6]),
            "y_increment": float(parts[7]),
            "y_origin": float(parts[8]),
            "y_reference": int(parts[9]),
        }

    def get_waveform_x_increment(self) -> float:
        """:WAVeform:XINCrement? — Query X-axis increment (seconds/sample)."""
        return float(self.query(":WAVeform:XINCrement?"))

    def get_waveform_x_origin(self) -> float:
        """:WAVeform:XORigin? — Query X-axis origin (seconds)."""
        return float(self.query(":WAVeform:XORigin?"))

    def get_waveform_x_reference(self) -> int:
        """:WAVeform:XREFerence? — Query X-axis reference point."""
        return int(self.query(":WAVeform:XREFerence?"))

    def get_waveform_y_increment(self) -> float:
        """:WAVeform:YINCrement? — Query Y-axis increment (volts/code)."""
        return float(self.query(":WAVeform:YINCrement?"))

    def get_waveform_y_origin(self) -> float:
        """:WAVeform:YORigin? — Query Y-axis origin (volts)."""
        return float(self.query(":WAVeform:YORigin?"))

    def get_waveform_y_reference(self) -> int:
        """:WAVeform:YREFerence? — Query Y-axis reference code."""
        return int(self.query(":WAVeform:YREFerence?"))

    def get_waveform_raw(self, channel: int) -> List[int]:
        """:WAVeform:DATA? — Fetch raw waveform data as unsigned integers.

        Args:
            channel: 1-4

        Returns:
            List of raw ADC codes (unsigned 8-bit or 16-bit).
        """
        self.set_waveform_source(channel)
        self.set_waveform_format("WORD")
        self.write(":WAVeform:BYTEorder LSBFirst")
        raw = self.query_binary_values(
            ":WAVeform:DATA?", datatype="H", is_big_endian=False
        )
        return [int(v) for v in raw]

    def get_waveform(self, channel: int) -> MeasurementResult:
        """Fetch calibrated waveform data for a channel.

        Queries :WAVeform:PREamble? and :WAVeform:DATA?, converts raw ADC
        codes to real voltage values using: V = (raw - yref) * yinc + yor
        and generates a time axis using: t = (n - xref) * xinc + xor

        Args:
            channel: 1-4

        Returns:
            MeasurementResult with value=(time_array, voltage_array), unit="V".
        """
        preamble = self.get_waveform_preamble()
        raw = self.get_waveform_raw(channel)

        y_inc = preamble["y_increment"]
        y_origin = preamble["y_origin"]
        y_ref = preamble["y_reference"]
        x_inc = preamble["x_increment"]
        x_origin = preamble["x_origin"]
        x_ref = preamble["x_reference"]

        voltage = [((v - y_ref) * y_inc) + y_origin for v in raw]
        time_axis = [
            ((n - x_ref) * x_inc) + x_origin for n in range(len(raw))
        ]

        if np is not None:
            time_arr = np.array(time_axis)
            voltage_arr = np.array(voltage)
        else:
            time_arr = time_axis
            voltage_arr = voltage

        return MeasurementResult(
            value=(time_arr, voltage_arr),
            unit="V",
            channel=channel,
            metadata={"preamble": preamble},
        )

    # ── Measurement Helpers (Oscilloscope interface) ───────────

    def measure_frequency(self, channel: int = 1) -> MeasurementResult:
        """:MEASure:FREQuency? — Measure frequency on a channel."""
        val = self.query(f":MEASure:FREQuency? CHANnel{channel}")
        return MeasurementResult(float(val), "Hz", channel=channel)

    def measure_duty_cycle(self, channel: int = 1) -> MeasurementResult:
        """:MEASure:DUTYcycle? — Measure duty cycle on a channel."""
        val = self.query(f":MEASure:DUTYcycle? CHANnel{channel}")
        return MeasurementResult(float(val), "%", channel=channel)

    def measure_v_peak_to_peak(self, channel: int = 1) -> MeasurementResult:
        """:MEASure:VPP? — Measure Vpp on a channel."""
        val = self.query(f":MEASure:VPP? CHANnel{channel}")
        return MeasurementResult(float(val), "V", channel=channel)

    def get_screenshot(self) -> bytes:
        """:DISPlay:DATA? — Capture display screenshot as PNG."""
        self.write(":DISPlay:DATA? PNG, COLor")
        return self.inst.read_raw()

    # ── Safety & Shutdown ──────────────────────────────────────

    def shutdown_safety(self) -> None:
        """Stop acquisition and sync."""
        self.stop()
        self.sync_config()
