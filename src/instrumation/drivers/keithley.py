from .base import Multimeter

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

    def measure_voltage(self) -> float:
        """Measures DC Voltage."""
        if self.resource:
            return float(self.resource.query(":MEAS:VOLT:DC?"))
        return 0.0

    def measure_resistance(self) -> float:
        """Measures 2-wire Resistance."""
        if self.resource:
            return float(self.resource.query(":MEAS:RES?"))
        return 0.0

    def measure_current(self) -> float:
        """Measures DC Current."""
        if self.resource:
            return float(self.resource.query(":MEAS:CURR:DC?"))
        return 0.0

    # Implement other abstract methods
    def measure_frequency(self) -> float:
        if self.resource:
             return float(self.resource.query(":MEAS:FREQ?"))
        return 0.0

    def measure_duty_cycle(self) -> float:
         # Keithley 2000 might not have direct duty cycle measurement?
         # Returning 0 for now as placeholder or simulation behavior
         return 0.0

    def measure_v_peak_to_peak(self) -> float:
         # Placeholder
         return 0.0
