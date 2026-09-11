from .base import Multimeter
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("DMM")
class KeithleyDMM6500(RealDriver, Multimeter):
    """Driver for Keithley DMM6500 6.5-digit Graphical Bench/System Multimeter.

    Uses the native ``SCPI`` command set (the DMM6500 also ships
    ``SCPI2000``/``SCPI34401`` legacy-compatible personalities, and a
    non-SCPI TSP scripting language, but this driver targets the default
    native set). Function selection is a string argument to
    ``:SENSe:FUNCtion``, distinct from the ``:CONFigure``-style dialect
    used by the Keysight 34461A/Fluke 884x/Siglent SDM3000 drivers:
    select the function, configure its ``:SENSe:<FUNC>:*`` subsystem,
    then trigger + read with ``:READ?``.

    SCPI Reference (DMM6500 Reference Manual):
        - :SENSe:FUNCtion "<VOLT:DC|VOLT:AC|CURR:DC|CURR:AC|RESistance|
          FRESistance|FREQuency|PERiod|CAPacitance|CONTinuity|DIODe|
          TEMPerature>"
        - :SENSe:<FUNC>:RANGe:AUTO {ON|OFF}
        - :SENSe:<FUNC>:NPLC <n>
        - :SENSe:<FUNC>:AZERo {ON|OFF}
        - :SENSe:FRESistance:OCOMpensated {ON|OFF} — offset compensation (4W)
        - :READ?                                     — trigger + read active function
        - *RST
    """

    def preset(self, automation_optimized: bool = True) -> None:
        self.write("*RST")
        self.wait_ready()

    def _select_function(self, func: str) -> None:
        self.safe_send(f'SENS:FUNC "{func}"')

    def configure_voltage_dc(self) -> None:
        self._select_function("VOLT:DC")

    def configure_voltage_ac(self) -> None:
        self._select_function("VOLT:AC")

    def measure_voltage(self, ac: bool = False) -> MeasurementResult:
        self._select_function("VOLT:AC" if ac else "VOLT:DC")
        val = self.query_ascii("READ?")
        return MeasurementResult(float(val), "V")

    def measure_resistance(self, four_wire: bool = False) -> MeasurementResult:
        self._select_function("FRES" if four_wire else "RES")
        val = self.query_ascii("READ?")
        return MeasurementResult(float(val), "Ohm")

    def measure_current(self, ac: bool = False) -> MeasurementResult:
        self._select_function("CURR:AC" if ac else "CURR:DC")
        val = self.query_ascii("READ?")
        return MeasurementResult(float(val), "A")

    def set_auto_range(self, state: bool, func: str = "VOLT:DC") -> None:
        val = "ON" if state else "OFF"
        self.safe_send(f"SENS:{func}:RANG:AUTO {val}")

    def set_nplc(self, plc: float, func: str = "VOLT:DC") -> None:
        """Sets the integration time (power-line cycles) for the given function."""
        self.safe_send(f"SENS:{func}:NPLC {plc}")

    def set_offset_compensation(self, state: bool) -> None:
        """Enables/disables offset compensation for 4-wire resistance."""
        self.safe_send(f"SENS:FRES:OCOM {'ON' if state else 'OFF'}")

    def measure_frequency(self) -> MeasurementResult:
        self._select_function("FREQ")
        val = self.query_ascii("READ?")
        return MeasurementResult(float(val), "Hz")

    def measure_period(self) -> MeasurementResult:
        self._select_function("PER")
        val = self.query_ascii("READ?")
        return MeasurementResult(float(val), "s")

    def measure_capacitance(self) -> MeasurementResult:
        self._select_function("CAP")
        val = self.query_ascii("READ?")
        return MeasurementResult(float(val), "F")

    def measure_continuity(self) -> MeasurementResult:
        self._select_function("CONT")
        val = self.query_ascii("READ?")
        return MeasurementResult(float(val), "Ohm")

    def measure_diode(self) -> MeasurementResult:
        self._select_function("DIOD")
        val = self.query_ascii("READ?")
        return MeasurementResult(float(val), "V")

    def measure_temperature(self) -> MeasurementResult:
        self._select_function("TEMP")
        val = self.query_ascii("READ?")
        return MeasurementResult(float(val), "C")

    def measure_duty_cycle(self) -> MeasurementResult:
        self._unsupported_feature("Duty Cycle")
        return MeasurementResult(0.0, "%")

    def measure_v_peak_to_peak(self) -> MeasurementResult:
        self._unsupported_feature("Vpp")
        return MeasurementResult(0.0, "V")

    def shutdown_safety(self) -> None:
        self.configure_voltage_dc()
        self.sync_config()
