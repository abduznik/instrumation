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

    def preset(self, automation_optimized: bool = True) -> None:
        self.write("*RST")
        self.wait_ready()

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
        val = self.query_ascii(":MEAS:FREQ?")
        return MeasurementResult(float(val), "Hz")

    def measure_period(self) -> MeasurementResult:
        val = self.query_ascii(":MEAS:PER?")
        return MeasurementResult(float(val), "s")

    def measure_temperature(self, probe_type: str = "TC", probe: str = "K") -> MeasurementResult:
        val = self.query_ascii(f":MEAS:TEMP? {probe_type},{probe}")
        return MeasurementResult(float(val), "C")

    def measure_capacitance(self) -> MeasurementResult:
        val = self.query_ascii(":MEAS:CAP?")
        return MeasurementResult(float(val), "F")

    def measure_diode(self) -> MeasurementResult:
        val = self.query_ascii(":MEAS:DIOD?")
        return MeasurementResult(float(val), "V")

    def measure_duty_cycle(self) -> MeasurementResult:
        self._unsupported_feature("Duty Cycle")
        return MeasurementResult(0.0, "%")

    def measure_v_peak_to_peak(self) -> MeasurementResult:
        self._unsupported_feature("Vpp")
        return MeasurementResult(0.0, "V")

    def shutdown_safety(self) -> None:
        self.set_auto_range(True)
        self.sync_config()
