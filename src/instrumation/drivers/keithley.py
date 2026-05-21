from .base import Multimeter, PowerSupply
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult

@register_driver("DMM")
class Keithley2000(RealDriver, Multimeter):
    """Driver for Keithley 2000 Series Digital Multimeters."""

    def preset(self, automation_optimized: bool = True):
        self.write("*RST")
        self.wait_ready()

    def configure_voltage_dc(self):
        self.safe_send(":CONF:VOLT:DC")

    def configure_voltage_ac(self):
        self.safe_send(":CONF:VOLT:AC")

    def measure_voltage(self, ac: bool = False) -> MeasurementResult:
        self.configure_voltage_ac() if ac else self.configure_voltage_dc()
        val = self.query_ascii(":READ?")
        return MeasurementResult(float(val.split(',')[0]), "V")

    def measure_resistance(self, four_wire: bool = False) -> MeasurementResult:
        cmd = ":CONF:FRES" if four_wire else ":CONF:RES"
        self.safe_send(cmd)
        val = self.query_ascii(":READ?")
        return MeasurementResult(float(val.split(',')[0]), "Ohm")

    def measure_current(self, ac: bool = False) -> MeasurementResult:
        cmd = ":CONF:CURR:AC" if ac else ":CONF:CURR:DC"
        self.safe_send(cmd)
        val = self.query_ascii(":READ?")
        return MeasurementResult(float(val.split(',')[0]), "A")

    def set_auto_range(self, state: bool):
        val = "ON" if state else "OFF"
        self.safe_send(f":VOLT:RANG:AUTO {val}")

    def measure_frequency(self) -> MeasurementResult:
        val = self.query_ascii(":MEAS:FREQ?")
        return MeasurementResult(float(val.split(',')[0]), "Hz")

    def measure_duty_cycle(self) -> MeasurementResult:
        self._unsupported_feature("Duty Cycle")
        return MeasurementResult(0.0, "%")

    def measure_v_peak_to_peak(self) -> MeasurementResult:
        self._unsupported_feature("Vpp")
        return MeasurementResult(0.0, "V")

    def shutdown_safety(self):
        self.set_auto_range(True)
        self.sync_config()

@register_driver("DMM")
@register_driver("PSU")
class Keithley2400(Keithley2000, PowerSupply):
    """Driver for Keithley 2400 Series SourceMeters (SMU).

    Operates as both a PowerSupply (source) and Multimeter (measure),
    making it a true Source Measure Unit.
    """

    def __init__(self, resource: str):
        super().__init__(resource)
        self.max_voltage = 210.0
        self.max_power_dbm = -999
        self._source_mode = "VOLT"

    def preset(self, automation_optimized: bool = True):
        self.write("*RST")
        self.safe_send(":SOUR:CLE:AUTO ON")
        self.wait_ready()

    # ── Source functions (PowerSupply) ─────────────────────────

    def set_voltage(self, voltage: float):
        self._validate_frequency(voltage)
        self._source_mode = "VOLT"
        self.safe_send(f":SOUR:VOLT {voltage}")

    def get_voltage(self) -> float:
        return float(self.query_ascii(":SOUR:VOLT?"))

    def set_current_limit(self, current: float):
        self._source_mode = "VOLT"
        self.safe_send(f":SOUR:CURR {current}")

    def set_current(self, current: float):
        self._source_mode = "CURR"
        self.safe_send(f":SOUR:CURR {current}")

    def get_current(self) -> MeasurementResult:
        return MeasurementResult(float(self.query_ascii(":SENS:CURR:DC?")), "A")

    def set_output(self, state: bool):
        self.safe_send(f":OUTP {'ON' if state else 'OFF'}")

    def get_output(self) -> bool:
        val = self.query_ascii(":OUTP?").strip()
        return val == "1"

    def set_ovp(self, voltage: float):
        self.safe_send(f":SOUR:VOLT:PROT {voltage}")

    def set_ocp(self, current: float):
        self.safe_send(f":SOUR:CURR:PROT {current}")

    def measure_voltage_actual(self) -> MeasurementResult:
        return self.measure_voltage()

    def clear_protection(self):
        self.safe_send(":SOUR:CLE:IMM")

    def set_voltage_range(self, voltage_range: float):
        self.safe_send(f":SOUR:VOLT:RANG {voltage_range}")

    def set_current_range(self, current_range: float):
        self.safe_send(f":SOUR:CURR:RANG {current_range}")

    def get_mode(self) -> str:
        val = self.query_ascii(":SOUR:FUNC?").strip().upper()
        if "VOLT" in val:
            return "CV"
        if "CURR" in val:
            return "CC"
        return "OFF"

    def measure_power(self) -> MeasurementResult:
        v = float(self.query_ascii(":MEAS:VOLT:DC?"))
        i = float(self.query_ascii(":MEAS:CURR:DC?"))
        return MeasurementResult(v * i, "W")

    # ── Measure functions (Multimeter) ─────────────────────────

    def configure_voltage_dc(self):
        self.safe_send(':SENS:FUNC "VOLT:DC"')

    def configure_voltage_ac(self):
        self._unsupported_feature("AC Voltage on 2400")
        self.safe_send(':SENS:FUNC "VOLT:DC"')

    def measure_voltage(self, ac: bool = False) -> MeasurementResult:
        if ac:
            self._unsupported_feature("AC Voltage")
        self.safe_send(':SENS:FUNC "VOLT:DC"')
        val = self.query_ascii(":READ?")
        # 2400 returns 4 values: V, I, RES, TIME
        return MeasurementResult(float(val.split(',')[0]), "V")

    def measure_resistance(self, four_wire: bool = False) -> MeasurementResult:
        self.safe_send(':SENS:FUNC "RES"')
        if four_wire:
            self.safe_send(':SYST:RSEN ON')
        else:
            self.safe_send(':SYST:RSEN OFF')
        val = self.query_ascii(":MEAS:RES?")
        return MeasurementResult(float(val.split(',')[2]), "Ohm")

    def measure_current(self, ac: bool = False) -> MeasurementResult:
        if ac:
            self._unsupported_feature("AC Current")
        self.safe_send(':SENS:FUNC "CURR:DC"')
        val = self.query_ascii(":READ?")
        return MeasurementResult(float(val.split(',')[1]), "A")

    def set_auto_range(self, state: bool):
        val = "ON" if state else "OFF"
        self.safe_send(f":SOUR:VOLT:RANG:AUTO {val}")

    def shutdown_safety(self):
        self.set_output(False)
        self.safe_send(":SOUR:VOLT 0")
        self.safe_send(":SOUR:CURR 0")
        self.sync_config()
