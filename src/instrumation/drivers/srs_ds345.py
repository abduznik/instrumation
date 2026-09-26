from .base import FunctionGenerator
from .registry import register_driver
from .real import RealDriver


@register_driver("SG")
class SRSDS345(RealDriver, FunctionGenerator):
    """Driver for Stanford Research Systems DS345 Synthesized Function/Arbitrary
    Waveform Generator.

    Uses SRS's distinctively terse, colon-free command mnemonics
    (``FREQ``, ``AMPL``, ``OFFS``, ``FUNC``, ``PHSE``) rather than a
    SCPI ``:SOURce:*`` subtree -- each takes a single positional
    argument, and waveform shape is a numeric code (0=sine, 1=square,
    2=triangle, 3=ramp, 4=noise, 5=arbitrary) instead of a mnemonic
    string. The DS345 has **no software output-enable command**: the
    configured waveform is always live on the output BNC, so
    ``set_output()`` logs an unsupported-feature warning and
    ``get_output()`` always reports ``True``.

    Command Reference (DS345 Operating Manual):
        - FREQ x    — sets output frequency to x Hz
        - AMPL x    — sets output amplitude (x with VP/VR/DB unit suffix)
        - OFFS x    — sets output offset to x volts
        - FUNC i    — sets waveform: 0=sine 1=square 2=triangle 3=ramp
                      4=noise 5=arbitrary
        - PHSE x    — sets waveform phase to x degrees
        - PCLR      — zeroes the current waveform phase
        - AECL      — sets output to ECL levels (1Vpp, -1.3V offset)
        - ATTL      — sets output to TTL levels (5Vpp, 2.5V offset)

    Unsupported: configure_list_sweep (no frequency-list sweep mode).
    """

    _FUNC_CODE = {"SIN": 0, "SQU": 1, "TRI": 2, "RAMP": 3, "NOIS": 4, "ARB": 5}
    _FUNC_NAME = {v: k for k, v in _FUNC_CODE.items()}

    def preset(self, automation_optimized: bool = True) -> None:
        self.write("*RST")
        self.wait_ready()

    def set_frequency(self, hz: float) -> None:
        self.write(f"FREQ {hz}")

    def get_frequency(self) -> float:
        return float(self.query("FREQ?"))

    def set_amplitude(self, dbm: float) -> None:
        self.write(f"AMPL {dbm}DB")

    def set_voltage(self, vpp: float) -> None:
        self.write(f"AMPL {vpp}VP")

    def set_offset(self, volts: float) -> None:
        self.write(f"OFFS {volts}")

    def set_waveform(self, shape: str) -> None:
        code = self._FUNC_CODE.get(shape.upper())
        if code is None:
            raise ValueError(f"Invalid waveform shape: {shape}")
        self.write(f"FUNC {code}")

    def get_waveform(self) -> str:
        code = int(self.query("FUNC?"))
        return self._FUNC_NAME.get(code, str(code))

    def set_phase(self, degrees: float) -> None:
        self.write(f"PHSE {degrees}")

    def zero_phase(self) -> None:
        """Zeroes the current waveform phase (PCLR)."""
        self.write("PCLR")

    def set_output(self, state: bool) -> None:
        self._unsupported_feature(
            "set_output (DS345 has no software output-enable command; "
            "the configured waveform is always live on the output BNC)"
        )

    def get_output(self) -> bool:
        return True

    def set_mod_state(self, mod_type: str, state: bool) -> None:
        self.write(f"MTYP {'1' if state else '0'}")

    def start_sweep(self, start: float, stop: float, points: int, dwell: float) -> None:
        self.write(f"SRAT {1.0 / dwell if dwell else 1.0}")
        self.write(f"SLIN 0")
        self.write(f"SFRQ {start}")
        self.write(f"SPAN {stop - start}")
        self.write("SSWP 1")

    def set_reference_clock(self, source: str) -> None:
        self.write(f"FSRC {1 if source.upper() == 'EXTERNAL' else 0}")

    def shutdown_safety(self) -> None:
        self.set_voltage(0.0)
        self.sync_config()
