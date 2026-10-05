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
        - MTYP i    — selects modulation type (0=lin sweep 1=log sweep
                      2=AM 3=FM 4=PM 5=burst); MENA i enables/disables it
        - STFR/SPFR — sweep start/stop frequency; RATE x — sweep rate in
                      Hz (= 1 / sweep time); sweep runs once MENA is set
        - *CLS      — clears status registers

    Unsupported: configure_list_sweep (no frequency-list sweep mode) and
    set_reference_clock (no reference-clock command; the rear-panel timebase
    input locks to an external 10 MHz on its own).
    """

    _FUNC_CODE = {"SIN": 0, "SQU": 1, "TRI": 2, "RAMP": 3, "NOIS": 4, "ARB": 5}
    _FUNC_NAME = {v: k for k, v in _FUNC_CODE.items()}
    _MOD_TYPE = {"SWEEP": 0, "AM": 2, "FM": 3, "PM": 4, "BURST": 5}

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
        # MTYP selects the modulation *type*; it is not an on/off switch.
        # MENA (modulation enable) is the boolean command.
        code = self._MOD_TYPE.get(mod_type.upper())
        if code is None:
            raise ValueError(
                f"Invalid modulation type: {mod_type} "
                f"(DS345 MTYP accepts {', '.join(self._MOD_TYPE)})"
            )
        self.write(f"MTYP {code}")
        self.write(f"MENA {1 if state else 0}")

    def start_sweep(self, start: float, stop: float, points: int, dwell: float) -> None:
        # On the DS345 a sweep is a modulation mode: set the bounds and rate,
        # select linear sweep (MTYP 0), then enable modulation (MENA 1).
        # RATE is the sweep rate in Hz, i.e. 1 / sweep time -- the manual's
        # sweep-time range is 1 ms to 1000 s, so 0.001..1000 Hz.
        total = dwell * points
        rate = min(max(1.0 / total if total > 0 else 1.0, 0.001), 1000.0)
        self.write(f"STFR {start}")
        self.write(f"SPFR {stop}")
        self.write(f"RATE {rate}")
        self.write("MTYP 0")
        self.write("MENA 1")

    def set_reference_clock(self, source: str) -> None:
        self._unsupported_feature(
            "set_reference_clock (the DS345 has no reference-clock command; "
            "the rear-panel timebase input locks to an external 10 MHz on "
            "its own)"
        )

    def sync_config(self) -> None:
        # The DS345 defines *CLS but no *WAI (zero hits in the operating
        # manual) -- *WAI would be an unrecognized command and set the
        # standard-event CMD error bit.
        self.write("*CLS")

    def wait_ready(self, timeout: float = 30.0) -> None:
        # No operation-complete mechanism on the DS345: *OPC? is undefined
        # and standard-event bit 0 is "unused". The only completion signal
        # (serial-poll NO COMMAND, bit 7) is GPIB-serial-poll-only -- the
        # manual states *STB? always reads 0 for it. Nothing to poll.
        return

    def check_errors(self) -> None:
        """No SYST:ERR? message queue on the DS345; command errors surface
        as standard-event status bits (*ESR? execution/command error)."""
        pass

    def _discover_options(self) -> None:
        """No *OPT? query on the DS345 -- feature set is fixed, no options."""
        self.options = []

    def shutdown_safety(self) -> None:
        self.set_voltage(0.0)
        self.sync_config()
