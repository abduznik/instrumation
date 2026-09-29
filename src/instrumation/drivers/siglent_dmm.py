from .base import Multimeter
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("DMM")
class SiglentSDM3055(RealDriver, Multimeter):
    """Driver for Siglent SDM3000 Series 5.5-digit Digital Multimeters.

    Validated Model: SDM3055. Standard SCPI-99 MEASure/CONFigure
    multimeter subsystem (same command shape as Keysight 34401A-family
    and Fluke 884x): DCV, ACV, DCI, ACI, 2W/4W resistance, frequency,
    period, capacitance, continuity, diode, temperature.

    SCPI Reference (SDM3000 Series Remote Manual, RC06035-E01A):
        - CONFigure[:VOLTage]:{AC|DC} [<range>|AUTO|MIN|MAX|DEF]
        - MEASure[:VOLTage]:{AC|DC}?
        - CONFigure:CURRent:{AC|DC} [<range>|AUTO|MIN|MAX|DEF]
        - MEASure:CURRent:{AC|DC}?
        - CONFigure:{RESistance|FRESistance} [<range>]
        - MEASure:{RESistance|FRESistance}?
        - CONFigure:{FREQuency|PERiod}
        - MEASure:{FREQuency|PERiod}?
        - CONFigure:CAPacitance [<range>|AUTO|MIN|MAX|DEF]
        - MEASure:CAPacitance?
        - CONFigure:CONTinuity / MEASure:CONTinuity?
        - CONFigure:DIODe / MEASure:DIODe?
        - CONFigure:TEMPerature [RTD|THERmistor|DEFault]
        - MEASure:TEMPerature? [RTD|THERmistor|DEFault]
        - [SENSe:]VOLTage[:DC]:NPLC {<PLC>|MIN|MAX|DEF}
        - [SENSe:]CURRent[:DC]:NPLC {<PLC>|MIN|MAX|DEF}
        - VOLTage:DC:RANGe:AUTO {ON|OFF}
        - *RST / *CLS / SYSTem:ERRor?
    """

    def configure_voltage_dc(self) -> None:
        self.safe_send("CONF:VOLT:DC")

    def configure_voltage_ac(self) -> None:
        self.safe_send("CONF:VOLT:AC")

    def measure_voltage(self, ac: bool = False) -> MeasurementResult:
        cmd = "MEAS:VOLT:AC?" if ac else "MEAS:VOLT:DC?"
        val = self.query_ascii(cmd)
        return MeasurementResult(float(val), "V")

    def measure_resistance(self, four_wire: bool = False) -> MeasurementResult:
        cmd = "MEAS:FRES?" if four_wire else "MEAS:RES?"
        val = self.query_ascii(cmd)
        return MeasurementResult(float(val), "Ohm")

    def measure_current(self, ac: bool = False) -> MeasurementResult:
        cmd = "MEAS:CURR:AC?" if ac else "MEAS:CURR:DC?"
        val = self.query_ascii(cmd)
        return MeasurementResult(float(val), "A")

    def set_auto_range(self, state: bool) -> None:
        val = "ON" if state else "OFF"
        self.safe_send(f"VOLT:DC:RANG:AUTO {val}")

    def measure_frequency(self) -> MeasurementResult:
        return self._meas("MEAS:FREQ?", "Hz")

    def measure_period(self) -> MeasurementResult:
        return self._meas("MEAS:PER?", "s")

    def measure_capacitance(self) -> MeasurementResult:
        return self._meas("MEAS:CAP?", "F")

    def measure_continuity(self) -> MeasurementResult:
        """Measures resistance in continuity-test mode (Ohms)."""
        return self._meas("MEAS:CONT?", "Ohm")

    def measure_diode(self) -> MeasurementResult:
        return self._meas("MEAS:DIOD?", "V")

    def measure_temperature(self, probe_type: str = "RTD", probe: str = "PT100") -> MeasurementResult:
        return self._meas(f"MEAS:TEMP? {probe_type},{probe}", "C")

    def set_nplc(self, plc: float, ac: bool = False) -> None:
        """Sets integration time in power-line cycles for the active DC/AC function."""
        subsystem = "CURR" if ac else "VOLT"
        self.safe_send(f"{subsystem}:DC:NPLC {plc}")

    def shutdown_safety(self) -> None:
        self.set_auto_range(True)
        self.sync_config()
