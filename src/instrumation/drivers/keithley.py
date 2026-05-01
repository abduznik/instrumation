from .base import Multimeter
from .registry import register_driver
from ..results import MeasurementResult

@register_driver("DMM")
class Keithley2000(Multimeter):
    def connect(self):
        if self.resource:
            self.connected = True
            self.resource.write("*CLS")

    def disconnect(self):
        if self.resource:
            self.resource.close()
        self.connected = False

    def get_id(self) -> str:
        if self.resource:
            return self.resource.query("*IDN?").strip()
        return "Not Connected"

    def measure_voltage(self) -> MeasurementResult:
        """Measures DC Voltage."""
        if self.resource:
            return MeasurementResult(float(self.resource.query(":MEAS:VOLT:DC?")), "V")
        return MeasurementResult(0.0, "V")

    def measure_resistance(self) -> MeasurementResult:
        """Measures 2-wire Resistance."""
        if self.resource:
            return MeasurementResult(float(self.resource.query(":MEAS:RES?")), "Ohm")
        return MeasurementResult(0.0, "Ohm")

    def measure_current(self) -> float:
        """Measures DC Current."""
        if self.resource:
            return float(self.resource.query(":MEAS:CURR:DC?"))
        return 0.0

    # Implement other abstract methods
    def measure_frequency(self) -> MeasurementResult:
        if self.resource:
             return MeasurementResult(float(self.resource.query(":MEAS:FREQ?")), "Hz")
        return MeasurementResult(0.0, "Hz")

    def measure_duty_cycle(self) -> MeasurementResult:
         # Keithley 2000 might not have direct duty cycle measurement?
         # Returning 0 for now as placeholder or simulation behavior
         return MeasurementResult(0.0, "%")

    def measure_v_peak_to_peak(self) -> MeasurementResult:
         # Placeholder
         return MeasurementResult(0.0, "Vpp")
