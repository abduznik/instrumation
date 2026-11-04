from typing import Optional, Union

from .base import PowerSupply
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("PSU")
class KepcoKLP(RealDriver, PowerSupply):
    """Driver for the Kepco KLP Series 1200 W programmable DC power supply.

    Single output; every KLP rating (KLP 10-150-1200, 20-120-1200,
    36-60-1200, 75-33-1200, 150-16-1200, 300-8-1200, 600-4-1200) shares
    this one command set. SCPI, but not a SCPI-99 PSU dialect: the
    ``[SOURce]`` keyword is optional so ``VOLTage``/``CURRent`` sit at the
    root (``VOLT``, ``CURR``) and the output state is plain ``OUTP``.

    Command Reference (KLP Developer's Guide, P/N 243-1138, Appendix B):
        - VOLT <v> / VOLT?           — programmed output voltage (B.48/B.49)
        - CURR <a> / CURR?           — programmed output current (B.36/B.37)
        - OUTP {ON|OFF|1|0} / OUTP?  — output enable, query returns 1/0 (B.34/B.35)
        - MEAS:VOLT? / MEAS:CURR?    — actual output voltage/current (B.31/B.30)
        - VOLT:PROT <v> / VOLT:PROT? — overvoltage protection (B.54/B.55)
        - CURR:PROT <a> / CURR:PROT? — overcurrent protection (B.42/B.43)
        - FUNC:MODE? {VOLT|CURR}     — operating mode (B.47), returns two fields
        - SYST:ERR?                  — error queue, ``0,"No error"`` when empty (B.92)
        - *IDN? / *RST / *CLS / *OPC? / *SAV / *RCL / *TRG (Appendix A)

    Programmed values are clamped in hardware: exceeding ``VOLT:LIMit:HIGH``
    or 80% of ``VOLT:PROT`` programs the limit instead and posts -301 to the
    error queue, which ``safe_send()`` surfaces as a ConfigurationError.

    Deliberately not driven:
        - ``VOLT:LIMit:HIGH`` / ``CURR:LIMit:HIGH`` (the "virtual model") and
          the ``SYST:PASSword`` / ``CALIbrate`` tree: password protected, and
          re-programming the virtual model forces the output off and rewrites
          both protection levels.
        - ``VOLT:PROT:CLE``: named in the VOLT:PROT prose but absent from
          Appendix B, so ``clear_protection()`` stays unsupported rather than
          sending an undocumented command.

    IEEE 488.2 coverage is partial: the KLP implements no ``*WAI`` and no
    ``*OPT?``, so ``sync_config()`` uses ``*CLS`` + ``*OPC?`` and option
    discovery is a no-op.
    """

    def _discover_options(self) -> None:
        # No *OPT? on the KLP (Appendix A has no options query).
        self.options = []

    def sync_config(self) -> None:
        # No *WAI either -- *OPC? is the only synchronisation primitive.
        self.write("*CLS")
        self.wait_ready()

    def set_voltage(self, voltage: float, channel: Optional[int] = None) -> None:
        self.safe_send(f"VOLT {voltage}")

    def get_voltage(self, channel: Optional[int] = None) -> float:
        """Programmed output voltage (``VOLT?``); use measure_voltage_actual for the readback."""
        return float(self.query_ascii("VOLT?"))

    def set_current_limit(self, current: float, channel: Optional[int] = None) -> None:
        self.safe_send(f"CURR {current}")

    def get_current(self, channel: Optional[int] = None) -> MeasurementResult:
        """Programmed current limit (``CURR?``); use measure_current for the readback."""
        return self._meas("CURR?", "A")

    def set_output(self, state: bool, channel: Optional[int] = None) -> None:
        self.safe_send(f"OUTP {'ON' if state else 'OFF'}")

    def get_output(self, channel: Optional[int] = None) -> bool:
        return self.query_ascii("OUTP?").strip().upper() in ("1", "ON")

    def set_ovp(self, voltage: float, channel: Optional[int] = None) -> None:
        """Sets the overvoltage trip point. The output is switched OFF by the instrument."""
        self.safe_send(f"VOLT:PROT {voltage}")

    def set_ocp(self, current: float, channel: Optional[int] = None) -> None:
        """Sets the overcurrent trip point. The output is switched OFF by the instrument."""
        self.safe_send(f"CURR:PROT {current}")

    def measure_voltage_actual(self, channel: Optional[int] = None) -> MeasurementResult:
        return self._meas("MEAS:VOLT?", "V")

    def measure_current(self, channel: Optional[int] = None) -> MeasurementResult:
        return self._meas("MEAS:CURR?", "A")

    def get_mode(self) -> str:
        """``CV``, ``CC`` or ``OFF``.

        ``FUNC:MODE?`` returns ``<actual>,<commanded>`` -- only the first
        field describes what the load is actually doing.
        """
        if not self.get_output():
            return "OFF"
        actual = self.query_ascii("FUNC:MODE?").split(",")[0].strip().upper()
        return {"VOLT": "CV", "CURR": "CC"}.get(actual, actual)

    def save_state(self, index: Union[int, str]) -> None:
        self.safe_send(f"*SAV {self._cell(index)}")

    def load_state(self, index: Union[int, str]) -> None:
        self.safe_send(f"*RCL {self._cell(index)}")

    @staticmethod
    def _cell(index: Union[int, str]) -> int:
        """KLP has 40 non-volatile cells, numbered 1-40 (A.11/A.12)."""
        cell = int(index)
        if not 1 <= cell <= 40:
            raise ValueError("KLP memory cell must be 1-40")
        return cell

    def shutdown_safety(self) -> None:
        self.set_output(False)
        self.set_voltage(0.0)
