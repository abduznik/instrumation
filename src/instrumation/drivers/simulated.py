import random
import time
import math
from .base import InstrumentDriver, Multimeter, PowerSupply, SpectrumAnalyzer, NetworkAnalyzer, Oscilloscope, SignalGenerator
from .registry import register_driver
from ..results import MeasurementResult

class SimulatedBaseDriver(InstrumentDriver):
    def __init__(self, resource: str, latency: float = 0.01):
        super().__init__(resource)
        self.latency = latency

    def connect(self):
        self.connected = True
        self.identity = {"manufacturer": "SIM", "model": "SIM_DRIVER", "serial": "123", "version": "1.0"}

    def disconnect(self): self.connected = False
    
    def write(self, command: str):
        print(f"[SIM] Write: {command}")
        time.sleep(self.latency)

    def safe_send(self, command: str):
        print(f"[SIM] Safe Send: {command}")
        time.sleep(self.latency)

    def query(self, command: str) -> str:
        print(f"[SIM] Query: {command}")
        time.sleep(self.latency)
        if "*IDN?" in command:
            return "SIM,SIM_DRIVER,123,1.0"
        if "SYST:ERR?" in command:
            return '+0,"No error"'
        if "*OPC?" in command:
            return "1"
        return "0"

    def query_ascii(self, command: str) -> str:
        return self.query(command)

    def query_binary_values(self, command: str, datatype: str = 'f', is_big_endian: bool = False) -> list:
        print(f"[SIM] Binary Query: {command}")
        time.sleep(self.latency * 2) # Binary takes a bit longer to simulate transfer
        return [random.uniform(-100, 0) for _ in range(1001)]

    def get_id(self): return "SIM_DRIVER"
    def preset(self, automation_optimized=True): pass
    def clear_status(self): pass
    def sync_config(self): pass
    def wait_ready(self, timeout=30): pass
    def shutdown_safety(self): pass
    def check_errors(self): pass
    def measure_frequency(self): return MeasurementResult(1000.0, "Hz")
    def measure_duty_cycle(self): return MeasurementResult(50.0, "%")
    def measure_v_peak_to_peak(self): return MeasurementResult(2.0, "V")

@register_driver("DMM")
class SimulatedMultimeter(SimulatedBaseDriver, Multimeter):
    def configure_voltage_dc(self): pass
    def configure_voltage_ac(self): pass
    def measure_voltage(self, ac=False): 
        time.sleep(self.latency)
        return MeasurementResult(5.0, "V")
    def measure_resistance(self, four_wire: bool = False): 
        time.sleep(self.latency)
        return MeasurementResult(1000.0, "Ohm")
    def measure_current(self, ac: bool = False): 
        time.sleep(self.latency)
        return MeasurementResult(0.01, "A")
    def set_auto_range(self, state): pass

@register_driver("PSU")
class SimulatedPowerSupply(SimulatedBaseDriver, PowerSupply):
    def set_voltage(self, voltage): 
        print(f"[SIM] Setting PSU Voltage: {voltage}")
    def get_voltage(self): return 0.0
    def set_current_limit(self, current): pass
    def get_current(self) -> float: return 0.0
    def get_current_limit(self) -> float: return 0.0
    def set_output(self, state): pass
    def get_output(self): return False
    def set_ovp(self, voltage): pass
    def set_ocp(self, current): pass
    def measure_voltage_actual(self) -> MeasurementResult:
        return MeasurementResult(0.0, "V")
    def measure_current(self) -> MeasurementResult:
        return MeasurementResult(0.0, "A")
    def clear_protection(self): pass

@register_driver("SA")
class SimulatedSpectrumAnalyzer(SimulatedBaseDriver, SpectrumAnalyzer):
    def peak_search(self): pass
    def get_marker_amplitude(self): 
        time.sleep(self.latency)
        return MeasurementResult(-20.0, "dBm")
    def set_center_freq(self, hz):
        self._validate_frequency(hz)
        self._center_freq = hz
        print(f"[SIM] Setting SA Center Freq: {hz}")
    def get_center_freq(self) -> float: return getattr(self, "_center_freq", 2.4e9)
    def set_span(self, hz): self._span = hz
    def get_span(self) -> float: return getattr(self, "_span", 100e6)
    def set_rbw(self, hz): pass
    def set_vbw(self, hz): pass
    def get_trace_data(self): return MeasurementResult([0.0]*1001, "dBm")

@register_driver("NA")
@register_driver("VNA")
class SimulatedNetworkAnalyzer(SimulatedBaseDriver, NetworkAnalyzer):
    def set_start_frequency(self, freq_hz): pass
    def set_stop_frequency(self, freq_hz): pass
    def set_points(self, num_points): pass
    def set_parameter(self, parameter: str):
        print(f"[SIM] VNA Setting Parameter: {parameter}")
    def get_trace_data(self, measurement_name: str = "CH1_S11_1"): 
        return MeasurementResult([random.uniform(-40, -10) for _ in range(201)], "dB")
    def get_complex_trace(self, measurement_name: str = "CH1_S11_1"): 
        # Generate some random complex numbers with magnitude between 0.01 and 0.3
        data = [complex(random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3)) for _ in range(201)]
        return MeasurementResult(data, "IQ")

@register_driver("SCOPE")
class SimulatedOscilloscope(SimulatedBaseDriver, Oscilloscope):
    def run(self): pass
    def stop(self): pass
    def single(self): pass
    def get_waveform(self, channel: int) -> MeasurementResult:
        data = [math.sin(i * 0.1) for i in range(1000)]
        return MeasurementResult(data, "V")
    def auto_scale(self): pass
    def set_trigger(self, source, level, slope): pass
    def get_screenshot(self): return b"SIM_SCREENSHOT"

@register_driver("SG")
class SimulatedSignalGenerator(SimulatedBaseDriver, SignalGenerator):
    def set_frequency(self, hz):
        self._validate_frequency(hz)
        print(f"[SIM] Setting SG Frequency: {hz}")
    def set_amplitude(self, dbm):
        self._validate_power(dbm)
        print(f"[SIM] Setting SG Amplitude: {dbm}")
    def set_output(self, state): pass
    def set_mod_state(self, mod_type, state): pass
    def start_sweep(self, start, stop, points, dwell): pass
    def configure_list_sweep(self, freq_list, power_list): pass
    def set_reference_clock(self, source): pass

class SimulatedDriver(SimulatedMultimeter):
    pass
