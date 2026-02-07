import random
import time
import math
from .base import InstrumentDriver, Multimeter, PowerSupply, SpectrumAnalyzer, NetworkAnalyzer

class SimulatedBaseDriver(InstrumentDriver):
    """Base class for all simulated drivers to provide standard SCPI-like behavior.

    Attributes:
        latency (float): Configurable delay to mimic real transport delays.
        responses (dict): Dictionary mapping SCPI commands to their simulated responses.
    """
    def __init__(self, resource, latency=0.01):
        super().__init__(resource)
        self.latency = latency
        self.responses = {
            "*IDN?": self.get_id,
            "*OPC?": "1",
            "*STB?": "0",
            "*ESR?": "0",
        }

    def _delay(self):
        """Injects a delay based on the configured latency."""
        if self.latency > 0:
            time.sleep(self.latency)

    def write(self, command: str):
        """Simulates writing a command to the instrument."""
        self._delay()
        print(f"[SIM] Write: {command}")

    def query(self, command: str) -> str:
        """Simulates querying the instrument with a SCPI command."""
        self._delay()
        response = self.responses.get(command.strip().upper(), "0")
        
        if callable(response):
            result = str(response())
        else:
            result = str(response)
            
        print(f"[SIM] Query: {command} -> {result}")
        return result

class SimulatedMultimeter(SimulatedBaseDriver, Multimeter):
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

class SimulatedPowerSupply(SimulatedBaseDriver, PowerSupply):
    def __init__(self, resource, latency=0.01):
        super().__init__(resource, latency)
        self.setpoint = 0.0
        self.current_limit = 1.0
        self.output_enabled = False

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

    def get_voltage(self) -> float:
        if self.output_enabled:
            return self.setpoint + random.gauss(0, 0.005)
        return 0.0

    def set_current_limit(self, current: float):
        print(f"[SIM-PSU] Current limit set to {current}A")
        self.current_limit = current

    def get_current(self) -> float:
        # Simulate load: I = V / R (assume 100 ohm load)
        if self.output_enabled and self.setpoint > 0:
            current = (self.setpoint / 100.0) + random.gauss(0, 0.001)
            return min(current, self.current_limit)
        return 0.0

    def set_output(self, state: bool):
        print(f"[SIM-PSU] Output {'ENABLED' if state else 'DISABLED'}")
        self.output_enabled = state

    def get_output(self) -> bool:
        return self.output_enabled

    def measure_frequency(self) -> float:
        return 1000.0 + random.gauss(0, 50.0)

    def measure_duty_cycle(self) -> float:
        return 50.0 + random.gauss(0, 5.0)

    def measure_v_peak_to_peak(self) -> float:
        return 2.0 + random.gauss(0, 0.1)

class SimulatedSpectrumAnalyzer(SimulatedBaseDriver, SpectrumAnalyzer):
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
        return 1000000000.0 + random.gauss(0, 10000000.0)

    def measure_duty_cycle(self) -> float:
        return 50.0 + random.gauss(0, 5.0)

    def measure_v_peak_to_peak(self) -> float:
        return 1.0 + random.gauss(0, 0.05)

class SimulatedNetworkAnalyzer(SimulatedBaseDriver, NetworkAnalyzer):
    def __init__(self, resource, latency=0.01):
        super().__init__(resource, latency)
        self.start_freq = 1e6
        self.stop_freq = 1e9
        self.points = 201

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
        print(f"[SIM-VNA] Getting trace for {measurement_name}")
        data = []
        for i in range(self.points):
             val = -20 + 10 * math.sin(i / self.points * 3.14) + random.gauss(0, 0.5)
             data.append(val)
        return data

    def measure_frequency(self) -> float:
        return 1000000000.0

    def measure_duty_cycle(self) -> float:
        return 0.0

    def measure_v_peak_to_peak(self) -> float:
        return 0.0

class SimulatedDriver(SimulatedMultimeter):
    pass
