import random
import time
from .base import Multimeter, PowerSupply, SpectrumAnalyzer

class SimulatedMultimeter(Multimeter):
    def connect(self):
        print("[SIM-DMM] Connected")
        self.connected = True

    def disconnect(self):
        print("[SIM-DMM] Disconnected")
        self.connected = False

    def get_id(self):
        return "SIM_DMM_X1000"

    def measure_voltage(self) -> float:
        # Simulate measuring a 5V rail with noise
        return 5.0 + random.gauss(0, 0.01)

    def measure_resistance(self) -> float:
        # Simulate a 1k resistor with noise
        return 1000.0 + random.gauss(0, 5.0)

class SimulatedPowerSupply(PowerSupply):
    def __init__(self, resource):
        super().__init__(resource)
        self.setpoint = 0.0

    def connect(self):
        print("[SIM-PSU] Connected")
        self.connected = True

    def disconnect(self):
        print("[SIM-PSU] Disconnected")
        self.connected = False

    def get_id(self):
        return "SIM_PSU_PRO"

    def set_voltage(self, voltage: float):
        print(f"[SIM-PSU] Output set to {voltage}V")
        self.setpoint = voltage

    def get_current(self) -> float:
        # Simulate load: I = V / R (assume 100 ohm load)
        if self.setpoint > 0:
            return (self.setpoint / 100.0) + random.gauss(0, 0.001)
        return 0.0

class SimulatedSpectrumAnalyzer(SpectrumAnalyzer):
    def connect(self):
        print("[SIM-SA] Connected")
        self.connected = True

    def disconnect(self):
        print("[SIM-SA] Disconnected")
        self.connected = False

    def get_id(self):
        return "SIM_SA_GEN3"

    def peak_search(self):
        print("[SIM-SA] Searching for peak...")
        time.sleep(0.2)

    def get_marker_amplitude(self) -> float:
        # Simulate a signal around -20 dBm
        return -20.0 + random.gauss(0, 0.5)

# Keep a generic SimulatedDriver for backward compatibility if needed, 
# or map it to DMM.
class SimulatedDriver(SimulatedMultimeter):
    pass