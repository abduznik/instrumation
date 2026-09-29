from .base import FunctionGenerator
from .registry import register_driver
from .real import RealDriver


@register_driver("SG")
class GWInstekMFG2000(RealDriver, FunctionGenerator):
    """Driver for GW Instek MFG-2000 Series Multi-Channel Function Generators.

    Validated Model: MFG-2120. Combines Rigol-style
    ``SOURce<n>:APPLy:<shape>`` waveform selection with a separate
    per-parameter SCPI subtree for frequency/amplitude/offset/phase
    (``SOURce<n>:FREQuency``, ``SOURce<n>:AMPLitude``,
    ``SOURce<n>:DCOffset``, ``SOURce<n>:PHASe``) -- unlike Rigol's
    single combined-argument ``APPLy`` call, MFG-2000 setpoints are
    each sent independently after selecting the waveform shape.

    SCPI Reference (MFG-2000 Series Programming Manual):
        - SOURce<n>:APPLy:{SINusoid|SQUare|RAMP|PULSe|NOISe|USER}
        - SOURce<n>:FREQuency <hz>
        - SOURce<n>:AMPLitude <vpp>
        - SOURce<n>:DCOffset <volts>
        - SOURce<n>:PHASe <degrees>
        - SOURce<n>:AM:STATe {ON|OFF}
        - SOURce<n>:FREQuency:STARt <hz> / :STOP <hz>
        - OUTPut<n> {ON|OFF}

    Unsupported: configure_list_sweep (no frequency-list sweep mode).
    """

    def __init__(self, resource: str, channel: int = 1) -> None:
        super().__init__(resource)
        self.channel = channel
        self._src = f"SOUR{channel}"

    def preset(self, automation_optimized: bool = True) -> None:
        self.write("*RST")
        self.wait_ready()

    def set_frequency(self, hz: float) -> None:
        self.write(f"{self._src}:FREQ {hz}")

    def set_amplitude(self, dbm: float) -> None:
        """AWGs use Voltage; converts dBm to Vpp (assumes 50 Ohm load)."""
        vpp = 2 * (10 ** ((dbm - 10) / 20))
        self.set_voltage(vpp)

    def set_voltage(self, vpp: float) -> None:
        self.write(f"{self._src}:AMP {vpp}")

    def set_offset(self, volts: float) -> None:
        self.write(f"{self._src}:DCO {volts}")

    def set_waveform(self, shape: str) -> None:
        shape_map = {
            "SIN": "SIN", "SQU": "SQU", "RAMP": "RAMP",
            "PULS": "PULS", "NOIS": "NOIS", "USER": "USER", "ARB": "USER",
        }
        name = shape_map.get(shape.upper(), shape.upper())
        self.write(f"{self._src}:APPL:{name}")

    def set_phase(self, degrees: float) -> None:
        self.write(f"{self._src}:PHAS {degrees}")

    def set_output(self, state: bool) -> None:
        self.write(f"OUTP{self.channel} {'ON' if state else 'OFF'}")

    def get_output(self) -> bool:
        resp = self.query(f"OUTP{self.channel}?")
        return resp.strip().upper() in ("1", "ON")

    def set_mod_state(self, mod_type: str, state: bool) -> None:
        self.write(f"{self._src}:{mod_type.upper()}:STAT {'ON' if state else 'OFF'}")

    def start_sweep(self, start: float, stop: float, points: int, dwell: float) -> None:
        self.write(f"{self._src}:FREQ:STAR {start}")
        self.write(f"{self._src}:FREQ:STOP {stop}")
        self.write(f"{self._src}:SWE:TIME {dwell * points}")
        self.write(f"{self._src}:SWE:STAT ON")

    def set_reference_clock(self, source: str) -> None:
        self.write(f"{self._src}:ROSC:SOUR {source.upper()}")

    def shutdown_safety(self) -> None:
        self.set_output(False)
        self.sync_config()
