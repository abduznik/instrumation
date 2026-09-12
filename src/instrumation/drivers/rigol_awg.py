from .base import FunctionGenerator
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("SG")
class RigolDG4000(RealDriver, FunctionGenerator):
    """Driver for Rigol DG4000 Series Function/Arbitrary Waveform Generators.

    Validated Model: DG4062. Uses the Agilent/Keysight-33500-derived
    ``[:SOURce[<n>]]:APPLy:<shape> <freq>,<amp>,<offset>,<phase>``
    single-command style shared across the DG1000Z/DG4000/DG5000
    families: one command sets frequency, amplitude, offset, and phase
    together, rather than Tektronix AFG3000's separate
    ``FREQuency:FIXed``/``VOLTage:AMPLitude`` subtree-per-parameter
    commands or Siglent SDG's comma-separated ``BSWV`` keyword.

    SCPI Reference (DG4000 Series Programming Guide):
        - [:SOURce[<n>]]:APPLy:SINusoid [<freq>[,<amp>[,<offset>[,<phase>]]]]
        - [:SOURce[<n>]]:APPLy:SQUare [<freq>[,<amp>[,<offset>[,<phase>]]]]
        - [:SOURce[<n>]]:APPLy:RAMP [<freq>[,<amp>[,<offset>[,<phase>]]]]
        - [:SOURce[<n>]]:APPLy:PULSe [<freq>[,<amp>[,<offset>[,<phase>]]]]
        - [:SOURce[<n>]]:APPLy:NOISe [<amp>[,<offset>]]
        - [:SOURce[<n>]]:APPLy:DC [<freq>,<amp_placeholder>,<offset>]
        - [:SOURce[<n>]]:FREQuency[:FIXed] <hz>
        - [:SOURce[<n>]]:VOLTage[:LEVel][:IMMediate][:AMPLitude] <vpp>
        - [:SOURce[<n>]]:VOLTage:OFFSet <volts>
        - [:SOURce[<n>]]:PHASe[:ADJust] <degrees>
        - OUTPut<n>[:STATe] {ON|OFF}
        - [:SOURce[<n>]]:SWEep:STATe {ON|OFF}
        - [:SOURce[<n>]]:ROSCillator:SOURce {INTernal|EXTernal}
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
        self.write(f"{self._src}:VOLT {vpp}")

    def set_offset(self, volts: float) -> None:
        self.write(f"{self._src}:VOLT:OFFS {volts}")

    def set_waveform(self, shape: str) -> None:
        shape_map = {
            "SIN": "SIN", "SQU": "SQU", "RAMP": "RAMP",
            "PULS": "PULS", "NOIS": "NOIS", "DC": "DC", "ARB": "ARB",
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

    def configure_list_sweep(self, freq_list: list, power_list: list) -> None:
        self._unsupported_feature("configure_list_sweep (use arbitrary-waveform list mode instead)")

    def set_reference_clock(self, source: str) -> None:
        self.write(f"{self._src}:ROSC:SOUR {source.upper()}")

    def measure_frequency(self) -> MeasurementResult:
        return MeasurementResult(0.0, "Hz")

    def measure_duty_cycle(self) -> MeasurementResult:
        return MeasurementResult(0.0, "%")

    def measure_v_peak_to_peak(self) -> MeasurementResult:
        return MeasurementResult(0.0, "V")

    def shutdown_safety(self) -> None:
        self.set_output(False)
        self.sync_config()
