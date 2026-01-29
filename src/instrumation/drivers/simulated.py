import random
import time
import math
from .base import Multimeter, PowerSupply, SpectrumAnalyzer, NetworkAnalyzer

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

    def measure_frequency(self) -> float:
        # Simulate frequency measurement (e.g., 1kHz signal with noise)
        return 1000.0 + random.gauss(0, 50.0)

    def measure_duty_cycle(self) -> float:
        # Simulate duty cycle measurement (percentage, 0-100%)
        return 50.0 + random.gauss(0, 5.0)

    def measure_v_peak_to_peak(self) -> float:
        # Simulate peak-to-peak voltage measurement
        return 2.0 + random.gauss(0, 0.1)

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

    def measure_frequency(self) -> float:
        # Simulate frequency measurement (e.g., 1kHz signal with noise)
        return 1000.0 + random.gauss(0, 50.0)

    def measure_duty_cycle(self) -> float:
        # Simulate duty cycle measurement (percentage, 0-100%)
        return 50.0 + random.gauss(0, 5.0)

    def measure_v_peak_to_peak(self) -> float:
        # Simulate peak-to-peak voltage measurement
        return 2.0 + random.gauss(0, 0.1)

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

    def measure_frequency(self) -> float:
        # Simulate frequency measurement (e.g., 1GHz signal with noise)
        return 1000000000.0 + random.gauss(0, 10000000.0)

    def measure_duty_cycle(self) -> float:
        # Simulate duty cycle measurement (percentage, 0-100%)
        return 50.0 + random.gauss(0, 5.0)

    def measure_v_peak_to_peak(self) -> float:
        # Simulate peak-to-peak voltage measurement
        return 1.0 + random.gauss(0, 0.05)

class SimulatedNetworkAnalyzer(NetworkAnalyzer):
    def connect(self):
        print("[SIM-VNA] Connected")
        self.connected = True

    def disconnect(self):
        print("[SIM-VNA] Disconnected")
        self.connected = False

    def get_id(self):
        return "SIM_VNA_E8363C"

    def set_start_frequency(self, freq_hz: float):
        print(f"[SIM-VNA] Start Freq set to {freq_hz} Hz")
        self.start_freq = freq_hz

    def set_stop_frequency(self, freq_hz: float):
        print(f"[SIM-VNA] Stop Freq set to {freq_hz} Hz")
        self.stop_freq = freq_hz

    def set_points(self, num_points: int):
        print(f"[SIM-VNA] Points set to {num_points}")
        self.points = num_points

    def get_trace_data(self, measurement_name: str) -> list[float]:
        # Generate fake S-parameter data (e.g., a filter shape)
        print(f"[SIM-VNA] Getting trace for {measurement_name}")
        points = getattr(self, 'points', 201)
        data = []
        for i in range(points):
             # Simple sine wave pattern to look like a filter
             val = -20 + 10 * math.sin(i / points * 3.14) + random.gauss(0, 0.5)
             data.append(val)
        return data

    def measure_frequency(self) -> float:
        # PNA usually measures frequency via markers or CW mode, but for ABC compliance:
        return 1000000000.0

    def measure_duty_cycle(self) -> float:
        # Not typical for VNA
        return 0.0

    def measure_v_peak_to_peak(self) -> float:
        # Not typical for VNA
        return 0.0

# Keep a generic SimulatedDriver for backward compatibility if needed, 
# or map it to DMM.
class SimulatedDriver(SimulatedMultimeter):
    pass