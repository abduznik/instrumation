from .base import Multimeter
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("DMM")
class RigolDM3068(RealDriver, Multimeter):
    """Driver for Rigol DM3000 Series 6.5-digit Digital Multimeters.

    Validated Model: DM3068. Unlike the SCPI-99 CONFigure/MEASure? split
    used by Keysight/Fluke/Siglent DMMs, the DM3000 series selects the
    active measurement function with ``:FUNCtion:*`` and then reads it
    back with a bare ``:MEASure:<FUNC>?`` query -- ``:MEASure:<FUNC>
    {<range>|MIN|MAX|DEF}`` (no ``?``) sets the range instead of
    triggering a fresh configure+read cycle.

    SCPI Reference (DM3000 Series Programming Guide):
        - :FUNCtion:VOLTage:DC / :FUNCtion:VOLTage:AC
        - :FUNCtion:CURRent:DC / :FUNCtion:CURRent:AC
        - :FUNCtion:RESistance / :FUNCtion:FRESistance
        - :FUNCtion:FREQuency / :FUNCtion:PERiod
        - :FUNCtion:CONTinuity / :FUNCtion:DIODe / :FUNCtion:CAPacitance
        - :MEASure:VOLTage:DC? / :MEASure:VOLTage:AC?
        - :MEASure:CURRent:DC? / :MEASure:CURRent:AC?
        - :MEASure:RESistance? / :MEASure:FRESistance?
        - :MEASure:FREQuency? / :MEASure:PERiod?
        - :MEASure:CAPacitance? / :MEASure:CONTinuity? / :MEASure:DIODe?
        - :MEASure {AUTO|MANU}       — global auto/manual ranging
        - :MEASure:RESistance:DIGIt / :MEASure:FRESistance:DIGIt {5|6|7|INC|DEC}
        - *IDN? / *RST
    """

    def preset(self, automation_optimized: bool = True) -> None:
        self.write("*RST")
        self.wait_ready()

    def configure_voltage_dc(self) -> None:
        self.safe_send(":FUNC:VOLT:DC")

    def configure_voltage_ac(self) -> None:
        self.safe_send(":FUNC:VOLT:AC")

    def measure_voltage(self, ac: bool = False) -> MeasurementResult:
        if ac:
            self.configure_voltage_ac()
            val = self.query_ascii(":MEAS:VOLT:AC?")
        else:
            self.configure_voltage_dc()
            val = self.query_ascii(":MEAS:VOLT:DC?")
        return MeasurementResult(float(val), "V")

    def measure_resistance(self, four_wire: bool = False) -> MeasurementResult:
        if four_wire:
            self.safe_send(":FUNC:FRES")
            val = self.query_ascii(":MEAS:FRES?")
        else:
            self.safe_send(":FUNC:RES")
            val = self.query_ascii(":MEAS:RES?")
        return MeasurementResult(float(val), "Ohm")

    def measure_current(self, ac: bool = False) -> MeasurementResult:
        if ac:
            self.safe_send(":FUNC:CURR:AC")
            val = self.query_ascii(":MEAS:CURR:AC?")
        else:
            self.safe_send(":FUNC:CURR:DC")
            val = self.query_ascii(":MEAS:CURR:DC?")
        return MeasurementResult(float(val), "A")

    def set_auto_range(self, state: bool) -> None:
        self.safe_send(f":MEAS {'AUTO' if state else 'MANU'}")

    def measure_frequency(self) -> MeasurementResult:
        self.safe_send(":FUNC:FREQ")
        val = self.query_ascii(":MEAS:FREQ?")
        return MeasurementResult(float(val), "Hz")

    def measure_period(self) -> MeasurementResult:
        self.safe_send(":FUNC:PER")
        val = self.query_ascii(":MEAS:PER?")
        return MeasurementResult(float(val), "s")

    def measure_capacitance(self) -> MeasurementResult:
        self.safe_send(":FUNC:CAP")
        val = self.query_ascii(":MEAS:CAP?")
        return MeasurementResult(float(val), "F")

    def measure_continuity(self) -> MeasurementResult:
        self.safe_send(":FUNC:CONT")
        val = self.query_ascii(":MEAS:CONT?")
        return MeasurementResult(float(val), "Ohm")

    def measure_diode(self) -> MeasurementResult:
        self.safe_send(":FUNC:DIOD")
        val = self.query_ascii(":MEAS:DIOD?")
        return MeasurementResult(float(val), "V")

    def set_digits(self, digits: str, four_wire: bool = False) -> None:
        """Sets display resolution for the active resistance function.

        Parameters
        ----------
        digits : str
            One of ``"5"``, ``"6"``, ``"7"``, ``"INC"``, ``"DEC"``.
        """
        subsystem = "FRES" if four_wire else "RES"
        self.safe_send(f":MEAS:{subsystem}:DIGIT {digits}")

    def measure_duty_cycle(self) -> MeasurementResult:
        self._unsupported_feature("Duty Cycle")
        return MeasurementResult(0.0, "%")

    def measure_v_peak_to_peak(self) -> MeasurementResult:
        self._unsupported_feature("Vpp")
        return MeasurementResult(0.0, "V")

    def shutdown_safety(self) -> None:
        self.configure_voltage_dc()
        self.sync_config()
