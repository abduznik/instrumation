from .base import FunctionGenerator
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("SG")
class SiglentSDG2000X(RealDriver, FunctionGenerator):
    """Driver for Siglent SDG2000X Series Arbitrary Waveform Generators.

    Validated Model: SDG2042X. Uses Siglent's ``C<n>:BSWV`` (Basic
    Wave) command: a single keyword takes comma-separated
    ``PARAM,value`` pairs rather than one SCPI subtree per parameter
    (e.g. ``C1:BSWV FRQ,1000`` sets frequency, ``C1:BSWV AMP,1`` sets
    amplitude) -- distinct from the Tektronix AFG3000's
    ``SOURce<n>:FREQuency:FIXed``-per-parameter dialect.

    SCPI Reference (SDG Series Programming Guide):
        - C<n>:BSWV WVTP,{SINE|SQUARE|RAMP|PULSE|NOISE|ARB|DC}
        - C<n>:BSWV FRQ,<hz>
        - C<n>:BSWV AMP,<vpp>
        - C<n>:BSWV OFST,<volts>
        - C<n>:BSWV PHSE,<degrees>
        - C<n>:OUTP {ON|OFF}
        - C<n>:OUTP?
        - C<n>:MDWV STATE,{ON|OFF}          — modulation on/off
        - C<n>:SWWV STATE,{ON|OFF}          — sweep on/off
        - C<n>:SWWV START,<hz>              — sweep start frequency
        - C<n>:SWWV STOP,<hz>               — sweep stop frequency
        - C<n>:SWWV TIME,<seconds>          — sweep time
    """

    def __init__(self, resource: str, channel: int = 1) -> None:
        super().__init__(resource)
        self.channel = channel
        self._ch = f"C{channel}"

    def preset(self, automation_optimized: bool = True) -> None:
        self.write("*RST")
        self.wait_ready()

    def set_frequency(self, hz: float) -> None:
        self.write(f"{self._ch}:BSWV FRQ,{hz}")

    def set_amplitude(self, dbm: float) -> None:
        """AWGs use Voltage; converts dBm to Vpp (assumes 50 Ohm load)."""
        vpp = 2 * (10 ** ((dbm - 10) / 20))
        self.set_voltage(vpp)

    def set_voltage(self, vpp: float) -> None:
        self.write(f"{self._ch}:BSWV AMP,{vpp}")

    def set_offset(self, volts: float) -> None:
        self.write(f"{self._ch}:BSWV OFST,{volts}")

    def set_waveform(self, shape: str) -> None:
        shape_map = {
            "SIN": "SINE", "SQU": "SQUARE", "PULS": "PULSE",
            "RAMP": "RAMP", "NOIS": "NOISE", "DC": "DC", "ARB": "ARB",
        }
        name = shape_map.get(shape.upper(), shape.upper())
        self.write(f"{self._ch}:BSWV WVTP,{name}")

    def set_phase(self, degrees: float) -> None:
        self.write(f"{self._ch}:BSWV PHSE,{degrees}")

    def set_output(self, state: bool) -> None:
        self.write(f"{self._ch}:OUTP {'ON' if state else 'OFF'}")

    def get_output(self) -> bool:
        resp = self.query(f"{self._ch}:OUTP?")
        return "ON" in resp.upper()

    def set_mod_state(self, mod_type: str, state: bool) -> None:
        self.write(f"{self._ch}:MDWV STATE,{'ON' if state else 'OFF'}")

    def start_sweep(self, start: float, stop: float, points: int, dwell: float) -> None:
        self.write(f"{self._ch}:SWWV START,{start}")
        self.write(f"{self._ch}:SWWV STOP,{stop}")
        self.write(f"{self._ch}:SWWV TIME,{dwell * points}")
        self.write(f"{self._ch}:SWWV STATE,ON")

    def configure_list_sweep(self, freq_list: list, power_list: list) -> None:
        self._unsupported_feature("configure_list_sweep (SDG2000X has no frequency-list sweep mode)")

    def set_reference_clock(self, source: str) -> None:
        self.write(f"ROSC {source.upper()}")

    def measure_frequency(self) -> MeasurementResult:
        return MeasurementResult(0.0, "Hz")

    def measure_duty_cycle(self) -> MeasurementResult:
        return MeasurementResult(0.0, "%")

    def measure_v_peak_to_peak(self) -> MeasurementResult:
        return MeasurementResult(0.0, "V")

    def shutdown_safety(self) -> None:
        self.set_output(False)
        self.sync_config()
