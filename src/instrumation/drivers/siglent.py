from .base import Oscilloscope, ElectronicLoad
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult

@register_driver("SCOPE")
class SiglentSDS(RealDriver, Oscilloscope):
    """Refined Driver for Siglent SDS Series Oscilloscopes."""

    def preset(self, automation_optimized: bool = True) -> None:
        self.write("*RST")
        self.wait_ready()

    def run(self) -> None: self.write("ARM")
    def stop(self) -> None: self.write("STOP")
    def single(self) -> None: self.write("SING")

    def get_waveform(self, channel: int) -> MeasurementResult:
        # Siglent requires reading raw bytes to handle its specific header
        self.write(f"C{channel}:WF? DAT2")
        raw_data = self.inst.read_raw()
        # Find where the data starts (after the header prefix 'Cx:WF DAT2,')
        header_prefix = f"C{channel}:WF DAT2,".encode()
        header_start = raw_data.find(header_prefix)
        if header_start != -1:
            data_start = header_start + len(header_prefix)
            # The data is everything after the header, excluding the last 2 bytes (footer)
            data_bytes = raw_data[data_start:-2]
            return MeasurementResult([float(b) for b in data_bytes], "V")
        return MeasurementResult([], "V")

    def auto_scale(self) -> None:
        self.safe_send("AUTOSCALE")

    def set_trigger(self, source: str, level: float, slope: str) -> None:
        self.safe_send(f"TRSE EDGE,SR,{source},HT,OFF")
        self.safe_send(f"{source}:TRLV {level}V")
        self.safe_send(f"{source}:TRSL {slope.upper()}")

    def get_screenshot(self) -> bytes:
        self.write("SCDP")
        return self.inst.read_raw()

    def _measure_pava(self, channel: int, param: str) -> float:
        resp = self.query_ascii(f"C{channel}:PAVA? {param}")
        # Parse "CHx:PAVA param,value unit"
        try:
            val_part = resp.split(',')[-1]
            # Remove unit (Hz, V, %, etc)
            val_str = "".join([c for c in val_part if c.isdigit() or c in ".-eE"])
            return float(val_str)
        except Exception:
            return 0.0

    def measure_frequency(self, channel: int = 1) -> MeasurementResult:
        val = self._measure_pava(channel, "FREQ")
        return MeasurementResult(val, "Hz")

    def measure_duty_cycle(self, channel: int = 1) -> MeasurementResult:
        val = self._measure_pava(channel, "DUTY")
        return MeasurementResult(val, "%")

    def measure_v_peak_to_peak(self, channel: int = 1) -> MeasurementResult:
        val = self._measure_pava(channel, "PKPK")
        return MeasurementResult(val, "V")

    # ── Comprehensive Auto-Measurements ──────────────────────────────

    def measure_v_max(self, channel: int = 1) -> MeasurementResult:
        """Measure maximum voltage on the given channel.

        SCPI: C{channel}:PAVA? VMAX
        """
        return MeasurementResult(self._measure_pava(channel, "VMAX"), "V")

    def measure_v_min(self, channel: int = 1) -> MeasurementResult:
        """Measure minimum voltage on the given channel.

        SCPI: C{channel}:PAVA? VMIN
        """
        return MeasurementResult(self._measure_pava(channel, "VMIN"), "V")

    def measure_v_rms(self, channel: int = 1) -> MeasurementResult:
        """Measure RMS voltage on the given channel.

        SCPI: C{channel}:PAVA? VRMS
        """
        return MeasurementResult(self._measure_pava(channel, "VRMS"), "V")

    def measure_v_amp(self, channel: int = 1) -> MeasurementResult:
        """Measure amplitude (top – base) on the given channel.

        SCPI: C{channel}:PAVA? VAMP
        """
        return MeasurementResult(self._measure_pava(channel, "VAMP"), "V")

    def measure_v_base(self, channel: int = 1) -> MeasurementResult:
        """Measure base voltage on the given channel.

        SCPI: C{channel}:PAVA? VBASE
        """
        return MeasurementResult(self._measure_pava(channel, "VBASE"), "V")

    def measure_v_overshoot(self, channel: int = 1) -> MeasurementResult:
        """Measure percentage overshoot on the given channel.

        SCPI: C{channel}:PAVA? VOVS
        """
        return MeasurementResult(self._measure_pava(channel, "VOVS"), "%")

    def measure_v_preshoot(self, channel: int = 1) -> MeasurementResult:
        """Measure percentage preshoot on the given channel.

        SCPI: C{channel}:PAVA? VPRE
        """
        return MeasurementResult(self._measure_pava(channel, "VPRE"), "%")

    def measure_rise_time(self, channel: int = 1) -> MeasurementResult:
        """Measure 10 %–90 % rise time on the given channel.

        SCPI: C{channel}:PAVA? RTIM
        """
        return MeasurementResult(self._measure_pava(channel, "RTIM"), "s")

    def measure_fall_time(self, channel: int = 1) -> MeasurementResult:
        """Measure 90 %–10 % fall time on the given channel.

        SCPI: C{channel}:PAVA? FTIM
        """
        return MeasurementResult(self._measure_pava(channel, "FTIM"), "s")

    def measure_period(self, channel: int = 1) -> MeasurementResult:
        """Measure signal period on the given channel.

        SCPI: C{channel}:PAVA? PERI
        """
        return MeasurementResult(self._measure_pava(channel, "PERI"), "s")

    # ── Channel Configuration ─────────────────────────────────────────

    def set_channel_scale(self, channel: int, volts_per_div: float) -> None:
        """Set the vertical scale (volts/div) for a channel.

        SCPI: C{channel}:SCAL {volts_per_div}
        """
        self.safe_send(f"C{channel}:SCAL {volts_per_div}")

    def set_channel_offset(self, channel: int, volts: float) -> None:
        """Set the vertical offset (volts) for a channel.

        SCPI: C{channel}:OFFS {volts}
        """
        self.safe_send(f"C{channel}:OFFS {volts}")

    def set_channel_coupling(self, channel: int, dc_ac_gnd: str) -> None:
        """Set the input coupling for a channel.

        Args:
            channel: Channel number (1–4).
            dc_ac_gnd: One of ``DC``, ``AC``, or ``GND``.

        SCPI: C{channel}:COUP {DC|AC|GND}
        """
        mode = dc_ac_gnd.upper()
        if mode not in ("DC", "AC", "GND"):
            raise ValueError(f"Invalid coupling: {dc_ac_gnd!r} — use DC, AC, or GND")
        self.safe_send(f"C{channel}:COUP {mode}")

    def set_channel_probe(self, channel: int, attenuation: float) -> None:
        """Set the probe attenuation factor for a channel.

        SCPI: C{channel}:PROB {attenuation}
        """
        self.safe_send(f"C{channel}:PROB {attenuation}")

    def set_channel_state(self, channel: int, on_off: str) -> None:
        """Turn a channel display on or off.

        Args:
            channel: Channel number (1–4).
            on_off: ``ON`` or ``OFF``.

        SCPI: C{channel}:TRL {ON|OFF}
        """
        state = on_off.upper()
        if state not in ("ON", "OFF"):
            raise ValueError(f"Invalid state: {on_off!r} — use ON or OFF")
        self.safe_send(f"C{channel}:TRL {state}")

    def channel_configure(
        self,
        channel: int,
        scale: float = None,
        offset: float = None,
        coupling: str = None,
        probe: float = None,
    ) -> None:
        """Convenience method to configure multiple channel parameters at once.

        Only non-None arguments are sent; omit a parameter to leave it
        unchanged on the instrument.

        Args:
            channel: Channel number (1–4).
            scale: Vertical scale in volts/div.
            offset: Vertical offset in volts.
            coupling: Input coupling — ``DC``, ``AC``, or ``GND``.
            probe: Probe attenuation factor (e.g. 1, 10).
        """
        if scale is not None:
            self.set_channel_scale(channel, scale)
        if offset is not None:
            self.set_channel_offset(channel, offset)
        if coupling is not None:
            self.set_channel_coupling(channel, coupling)
        if probe is not None:
            self.set_channel_probe(channel, probe)

    # ── Math Functions ────────────────────────────────────────────────

    def set_math_function(self, ch1: int, ch2: int, operation: str) -> None:
        """Set the math waveform operation between two channels.

        Args:
            ch1: First channel (1–4).
            ch2: Second channel (1–4).
            operation: Arithmetic operation — ``ADD``, ``SUB``, ``MUL``,
                or ``INV`` (inverts ch1).

        SCPI: MATH:AUX:MATH:{OP},{ch1},{ch2}
        """
        op = operation.upper()
        if op not in ("ADD", "SUB", "MUL", "INV"):
            raise ValueError(f"Invalid operation: {operation!r} — use ADD, SUB, MUL, or INV")
        self.safe_send(f"MATH:AUX:MATH:{op},C{ch1},C{ch2}")

    def enable_math(self, state: str) -> None:
        """Enable or disable the math waveform display.

        Args:
            state: ``ON`` or ``OFF``.

        SCPI: MATH:STAT ON|OFF
        """
        s = state.upper()
        if s not in ("ON", "OFF"):
            raise ValueError(f"Invalid state: {state!r} — use ON or OFF")
        self.safe_send(f"MATH:STAT {s}")

    def shutdown_safety(self) -> None:
        self.stop()
        self.sync_config()

@register_driver("LOAD")
@register_driver("ELOAD")
class SiglentSDL1000X(RealDriver, ElectronicLoad):
    """Driver for Siglent SDL1000X series DC Electronic Loads."""

    def preset(self, automation_optimized: bool = True) -> None:
        self.write("*RST")
        self.wait_ready()

    def set_mode(self, mode: str) -> None:
        # Siglent SDL modes: CC, CV, CR, CP
        mode_upper = mode.upper()
        if mode_upper not in ["CC", "CV", "CR", "CP"]:
            raise ValueError(f"Invalid mode: {mode}")
        self.safe_send(f":SOUR:FUNC {mode_upper}")

    def get_mode(self) -> str:
        return self.query_ascii(":SOUR:FUNC?").strip()

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

    def shutdown_safety(self) -> None:
        self.set_input(False)
        self.sync_config()
