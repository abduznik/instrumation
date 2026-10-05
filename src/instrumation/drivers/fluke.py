from .base import Multimeter
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("DMM")
class Fluke8846A(RealDriver, Multimeter):
    """Driver for Fluke 8845A/8846A 6.5-digit Digital Multimeters.

    DCV, ACV, DCI, ACI, 2W/4W Resistance, Frequency, Period,
    Temperature, Capacitance, and Diode test via SCPI (IEEE 488.2).
    """

    def configure_voltage_dc(self) -> None:
        self.safe_send(":CONF:VOLT:DC")

    def configure_voltage_ac(self) -> None:
        self.safe_send(":CONF:VOLT:AC")

    def measure_voltage(self, ac: bool = False) -> MeasurementResult:
        if ac:
            val = self.query_ascii(":MEAS:VOLT:AC?")
        else:
            val = self.query_ascii(":MEAS:VOLT:DC?")
        return MeasurementResult(float(val), "V")

    def measure_resistance(self, four_wire: bool = False) -> MeasurementResult:
        cmd = ":MEAS:FRES?" if four_wire else ":MEAS:RES?"
        val = self.query_ascii(cmd)
        return MeasurementResult(float(val), "Ohm")

    def measure_current(self, ac: bool = False) -> MeasurementResult:
        if ac:
            val = self.query_ascii(":MEAS:CURR:AC?")
        else:
            val = self.query_ascii(":MEAS:CURR:DC?")
        return MeasurementResult(float(val), "A")

    def set_auto_range(self, state: bool) -> None:
        val = "ON" if state else "OFF"
        self.safe_send(f":VOLT:RANG:AUTO {val}")

    def measure_frequency(self) -> MeasurementResult:
        return self._meas(":MEAS:FREQ?", "Hz")

    def measure_period(self) -> MeasurementResult:
        return self._meas(":MEAS:PER?", "s")

    def measure_temperature(self, four_wire: bool = False, rtd_type: str = "") -> MeasurementResult:
        """Measure temperature with an RTD probe (Pt100).

        The 8845A/8846A has no thermocouple support: ``MEASure:TEMPerature``
        only exposes ``:RTD?`` (2-wire) and ``:FRTD?`` (4-wire), each taking an
        optional RTD type (``PT100_385`` | ``PT100_392`` | ``CUST1``). There is
        no bare ``:TEMPerature?`` leaf query, so ``probe``-style arguments are
        not accepted (issue #260).

        Args:
            four_wire: Use the 4-wire (FRTD) input instead of 2-wire (RTD).
            rtd_type: Optional RTD type selector; empty keeps the meter's
                configured type.
        """
        cmd = ":MEAS:TEMP:FRTD?" if four_wire else ":MEAS:TEMP:RTD?"
        if rtd_type:
            cmd += f" {rtd_type}"
        return self._meas(cmd, "C")

    def measure_capacitance(self) -> MeasurementResult:
        return self._meas(":MEAS:CAP?", "F")

    def measure_diode(self) -> MeasurementResult:
        return self._meas(":MEAS:DIOD?", "V")

    def shutdown_safety(self) -> None:
        self.set_auto_range(True)
        self.sync_config()
