from .base import Multimeter
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
        # Keithley sometimes returns multiple values; take the first one
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
class Keithley2400(Keithley2000):
    """Driver for Keithley 2400 Series SourceMeters."""
    
    def set_output(self, state: bool):
        """Safety: Enable/Disable the source output."""
        self.write(f":OUTP {'ON' if state else 'OFF'}")

    def measure_resistance(self, four_wire: bool = False) -> MeasurementResult:
        """SourceMeters require sourcing before measuring resistance."""
        # Standard universal sequence for 2400
        self.safe_send(':SENS:FUNC "RES"')
        if four_wire:
            self.safe_send(':SYST:RSEN ON')
        else:
            self.safe_send(':SYST:RSEN OFF')
        val = self.query_ascii(":MEAS:RES?")
        return MeasurementResult(float(val.split(',')[2]), "Ohm") # Resistance is 3rd value in default return

    def shutdown_safety(self):
        self.set_output(False)
        super().shutdown_safety()
