import random
import time
import math
from .base import InstrumentDriver, Multimeter, PowerSupply, SpectrumAnalyzer, NetworkAnalyzer, Oscilloscope, FunctionGenerator, ElectronicLoad
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
    def save_state(self, index): print(f"[SIM] Saving state to {index}")
    def load_state(self, index): print(f"[SIM] Loading state from {index}")
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
    def set_voltage(self, voltage: float): 
        print(f"[SIM] Setting PSU Voltage: {voltage}")
        self._voltage = voltage
    def get_voltage(self) -> float: return getattr(self, "_voltage", 0.0)
    def set_current_limit(self, current: float): pass
    def get_current(self) -> MeasurementResult:
        time.sleep(self.latency)
        return MeasurementResult(0.0, "A")
    def get_current_limit(self) -> float: return 0.0
    def set_output(self, state: bool): self._output = state
    def get_output(self) -> bool: return getattr(self, "_output", False)
    def set_ovp(self, voltage: float): pass
    def set_ocp(self, current: float): pass
    def measure_voltage_actual(self) -> MeasurementResult:
        return MeasurementResult(0.0, "V")
    def measure_current(self) -> MeasurementResult:
        return MeasurementResult(0.0, "A")
    def clear_protection(self): pass
    def measure_power(self) -> MeasurementResult:
        return MeasurementResult(0.0, "W")
    def set_foldback_mode(self, mode: str): pass
    def set_foldback_delay(self, seconds: float): pass
    def set_autostart(self, state: bool): pass
    def get_mode(self) -> str: return "CV"

@register_driver("SA")
class SimulatedSpectrumAnalyzer(SimulatedBaseDriver, SpectrumAnalyzer):
    def __init__(self, resource: str, latency: float = 0.01):
        super().__init__(resource, latency)
        self._center_freq = 2.4e9
        self._span = 100e6
        self._sweep_data: list[tuple[float, float]] = []

    def _generate_sweep_data(self):
        num_points = 1001
        start_freq = self._center_freq - self._span / 2
        stop_freq = self._center_freq + self._span / 2
        self._sweep_data = []
        for i in range(num_points):
            freq = start_freq + (stop_freq - start_freq) * i / (num_points - 1)
            amp = random.uniform(-100, -60)
            self._sweep_data.append((freq, amp))
        peak_idx = random.randint(0, num_points - 1)
        freq, _ = self._sweep_data[peak_idx]
        self._sweep_data[peak_idx] = (freq, random.uniform(-30, -10))

    def peak_search(self):
        if not self._sweep_data:
            self._generate_sweep_data()
        max_idx = max(range(len(self._sweep_data)), key=lambda i: self._sweep_data[i][1])
        freq, amp = self._sweep_data[max_idx]
        return MeasurementResult(freq, "Hz"), MeasurementResult(amp, "dBm")

    def get_marker_amplitude(self): 
        time.sleep(self.latency)
        return MeasurementResult(-20.0, "dBm")
    def set_center_freq(self, hz):
        self._validate_frequency(hz)
        self._center_freq = hz
        self._sweep_data = []
        print(f"[SIM] Setting SA Center Freq: {hz}")
    def get_center_freq(self) -> float: return self._center_freq
    def set_span(self, hz):
        self._span = hz
        self._sweep_data = []
    def get_span(self) -> float: return self._span
    def set_rbw(self, hz): pass
    def set_vbw(self, hz): pass
    def get_trace_data(self):
        if not self._sweep_data:
            self._generate_sweep_data()
        amps = [amp for _, amp in self._sweep_data]
        return MeasurementResult(amps, "dBm")

@register_driver("NA")
@register_driver("VNA")
class SimulatedNetworkAnalyzer(SimulatedBaseDriver, NetworkAnalyzer):
    def set_start_frequency(self, freq_hz): pass
    def set_stop_frequency(self, freq_hz): pass
    def set_center_frequency(self, freq_hz): pass
    def set_span(self, span_hz): pass
    def set_points(self, num_points): pass
    def set_if_bandwidth(self, hz: float): pass
    def set_power_level(self, dbm: float): pass
    def set_sweep_type(self, sweep_type: str): pass
    def set_averaging(self, state: bool, count: int = 10): pass
    def set_continuous(self, state: bool): pass
    def set_parameter(self, parameter: str):
        print(f"[SIM] VNA Setting Parameter: {parameter}")
    def get_trace_data(self, measurement_name: str = "CH1_S11_1"): 
        return MeasurementResult([random.uniform(-40, -10) for _ in range(201)], "dB")
    def get_complex_trace(self, measurement_name: str = "CH1_S11_1"): 
        # Generate some random complex numbers with magnitude between 0.01 and 0.3
        data = [complex(random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3)) for _ in range(201)]
        return MeasurementResult(data, "IQ")

    def get_smith_data(self, measurement_name: str = "CH1_S11_1") -> MeasurementResult:
        """Simulates the VNA's built-in Smith math (R + jX)."""
        print(f"[SIM] VNA Native Smith Engine: {measurement_name}")
        # Return R + jX centered around 50 ohms
        data = [complex(random.uniform(45, 55), random.uniform(-2, 2)) for _ in range(201)]
        return MeasurementResult(data, "Z")

    def peak_search(self, marker: int = 1): pass
    def get_marker_x(self, marker: int = 1) -> float: return 2.4e9
    def get_marker_y(self, marker: int = 1) -> float: return -10.0
    def save_state(self, filename: str): pass
    def load_state(self, filename: str): pass
    def wait_for_sweep(self):
        time.sleep(0.5) # Simulate sweep time

@register_driver("SCOPE")
class SimulatedOscilloscope(SimulatedBaseDriver, Oscilloscope):
    def run(self): pass
    def stop(self): pass
    def single(self): pass
    def get_waveform(self, channel: int) -> MeasurementResult:
        data = [0.75 if math.sin(i * 0.1) >= 0 else -0.75 for i in range(1000)]
        return MeasurementResult(data, "V")
    def auto_scale(self): pass
    def set_trigger(self, source, level, slope): pass
    def get_screenshot(self): return b"SIM_SCREENSHOT"

@register_driver("SG")
class SimulatedSignalGenerator(SimulatedBaseDriver, FunctionGenerator):
    def __init__(self, resource: str):
        super().__init__(resource)
        self.max_power_dbm = 25.0
        self.max_frequency = 50e9

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
    def set_voltage(self, vpp): pass
    def set_offset(self, volts): pass
    def set_waveform(self, shape):
        print(f"[SIM] Setting Waveform: {shape}")


@register_driver("DMM")
@register_driver("PSU")
class SimulatedKeithley2400(SimulatedBaseDriver, Multimeter, PowerSupply):
    """Simulated Keithley 2400 SourceMeter."""

    def __init__(self, resource: str):
        super().__init__(resource)
        self._voltage = 0.0
        self._current = 0.0
        self._current_limit = 0.1
        self._output = False
        self._source_mode = "VOLT"

    def connect(self):
        super().connect()
        self.identity = {"manufacturer": "KEITHLEY", "model": "2400", "serial": "SIM-2400", "version": "1.0"}

    def get_id(self): return "KEITHLEY,2400,SIM-2400,1.0"

    # ── PowerSupply ────────────────────────────────────────
    def set_voltage(self, voltage):
        self._voltage = voltage
        print(f"[SIM] K2400 Source Voltage: {voltage} V")
    def get_voltage(self) -> float:
        return self._voltage
    def set_current_limit(self, current):
        self._current_limit = current
        print(f"[SIM] K2400 Compliance: {current} A")
    def set_current(self, current):
        self._current = current
        self._source_mode = "CURR"
        print(f"[SIM] K2400 Source Current: {current} A")
    def get_current(self) -> MeasurementResult:
        return MeasurementResult(self._current if self._source_mode == "CURR" else 0.0, "A")
    def set_output(self, state):
        self._output = state
        print(f"[SIM] K2400 Output: {'ON' if state else 'OFF'}")
    def get_output(self) -> bool:
        return self._output
    def set_ovp(self, voltage):
        print(f"[SIM] K2400 OVP: {voltage} V")
    def set_ocp(self, current):
        print(f"[SIM] K2400 OCP: {current} A")
    def measure_voltage_actual(self) -> MeasurementResult:
        return MeasurementResult(self._voltage, "V")
    def clear_protection(self):
        print("[SIM] K2400 Clear Protection")
    def measure_power(self) -> MeasurementResult:
        return MeasurementResult(self._voltage * 0.05, "W")
    def get_mode(self) -> str:
        return "CV" if self._source_mode == "VOLT" else "CC"

    # ── Multimeter ─────────────────────────────────────────
    def configure_voltage_dc(self): pass
    def configure_voltage_ac(self):
        print("[SIM] K2400: AC voltage not supported, configuring DC voltage instead")
        self._source_mode = "VOLT"
    def measure_voltage(self, ac=False):
        return MeasurementResult(self._voltage if self._voltage != 0.0 else 5.0, "V")
    def measure_resistance(self, four_wire=False):
        return MeasurementResult(1000.0, "Ohm")
    def measure_current(self, ac=False):
        return MeasurementResult(0.01, "A")
    def set_auto_range(self, state): pass


@register_driver("DMM")
class SimulatedKeysight34461A(SimulatedBaseDriver, Multimeter):
    """Simulated Keysight 34461A Truevolt DMM."""

    def __init__(self, resource: str):
        super().__init__(resource)
        self._auto_range = True

    def connect(self):
        super().connect()
        self.identity = {"manufacturer": "KEYSIGHT", "model": "34461A", "serial": "SIM-34461A", "version": "1.0"}

    def get_id(self): return "KEYSIGHT,34461A,SIM-34461A,1.0"

    def configure_voltage_dc(self): pass
    def configure_voltage_ac(self): pass
    def measure_voltage(self, ac=False):
        val = 4.95 if not ac else 4.90
        return MeasurementResult(val, "V")
    def measure_resistance(self, four_wire=False):
        return MeasurementResult(1000.0, "Ohm")
    def measure_current(self, ac=False):
        val = 0.05 if not ac else 0.04
        return MeasurementResult(val, "A")
    def set_auto_range(self, state):
        self._auto_range = state
    def measure_frequency(self):
        return MeasurementResult(1000.0, "Hz")
    def measure_period(self):
        return MeasurementResult(0.001, "s")
    def measure_temperature(self, probe_type="TC", probe="K"):
        return MeasurementResult(23.5, "C")
    def measure_capacitance(self):
        return MeasurementResult(10e-6, "F")
    def measure_diode(self):
        return MeasurementResult(0.6, "V")
    def measure_duty_cycle(self):
        return MeasurementResult(50.0, "%")
    def measure_v_peak_to_peak(self):
        return MeasurementResult(2.0, "V")


@register_driver("LOAD")
@register_driver("ELOAD")
class SimulatedElectronicLoad(SimulatedBaseDriver, ElectronicLoad):
    def __init__(self, resource: str):
        super().__init__(resource)
        self.max_voltage = 150.0
        self.max_current = 30.0
        self.max_power = 200.0

        self._mode = "CC"
        self._input_enabled = False

        self._target_current = 0.0
        self._target_voltage = 0.0
        self._target_resistance = 10.0
        self._target_power = 0.0

        self._ovp_limit = 60.0
        self._ocp_limit = 30.0
        self._opp_limit = 150.0
        self._protection_tripped = False

        self.source_voltage = 12.0
        self.source_resistance = 0.05

    def connect(self):
        super().connect()
        self.identity = {"manufacturer": "SIM", "model": "SIM_ELOAD_3000", "serial": "456", "version": "1.0"}

    def get_id(self):
        return "SIM_ELOAD_3000"

    def set_mode(self, mode: str):
        mode_upper = mode.upper()
        if mode_upper not in ["CC", "CV", "CR", "CP"]:
            raise ValueError(f"Invalid electronic load mode: {mode}")
        self._mode = mode_upper
        print(f"[SIM] Electronic Load Mode set to: {self._mode}")

    def get_mode(self) -> str:
        return self._mode

    def set_current(self, amps: float):
        if amps < 0 or amps > self.max_current:
            raise ValueError(f"Current {amps} A is out of instrument range (0 to {self.max_current} A)")
        self._target_current = amps

    def get_current(self) -> float:
        return self._target_current

    def set_voltage(self, volts: float):
        if volts < 0 or volts > self.max_voltage:
            raise ValueError(f"Voltage {volts} V is out of instrument range (0 to {self.max_voltage} V)")
        self._target_voltage = volts

    def get_voltage(self) -> float:
        return self._target_voltage

    def set_resistance(self, ohms: float):
        if ohms <= 0 or ohms > 100000.0:
            raise ValueError(f"Resistance {ohms} Ohm is out of valid range")
        self._target_resistance = ohms

    def get_resistance(self) -> float:
        return self._target_resistance

    def set_power(self, watts: float):
        if watts < 0 or watts > self.max_power:
            raise ValueError(f"Power {watts} W is out of instrument range (0 to {self.max_power} W)")
        self._target_power = watts

    def get_power(self) -> float:
        return self._target_power

    def set_input(self, state: bool):
        if state and self._protection_tripped:
            raise RuntimeError(f"Cannot enable input: Protection tripped ({self._protection_tripped})")
        self._input_enabled = state
        print(f"[SIM] Electronic Load input state: {'ON' if state else 'OFF'}")
        if state:
            self._update_physics()

    def get_input(self) -> bool:
        return self._input_enabled

    def set_ovp(self, voltage: float):
        self._ovp_limit = voltage

    def set_ocp(self, current: float):
        self._ocp_limit = current

    def set_opp(self, power: float):
        self._opp_limit = power

    def clear_protection(self):
        self._protection_tripped = False
        print("[SIM] Electronic Load protection cleared.")

    def _update_physics(self) -> tuple:
        if not self._input_enabled or self._protection_tripped:
            return self.source_voltage, 0.0, 0.0

        v_act, i_act, p_act = 0.0, 0.0, 0.0

        if self._mode == "CC":
            i_max = self.source_voltage / self.source_resistance
            i_act = min(self._target_current, i_max)
            v_act = max(0.0, self.source_voltage - i_act * self.source_resistance)
            p_act = v_act * i_act

        elif self._mode == "CV":
            if self._target_voltage >= self.source_voltage:
                i_act = 0.0
                v_act = self.source_voltage
            else:
                i_act = (self.source_voltage - self._target_voltage) / self.source_resistance
                v_act = self._target_voltage
            p_act = v_act * i_act

        elif self._mode == "CR":
            i_act = self.source_voltage / (self.source_resistance + self._target_resistance)
            v_act = i_act * self._target_resistance
            p_act = v_act * i_act

        elif self._mode == "CP":
            disc = (self.source_voltage ** 2) - (4 * self.source_resistance * self._target_power)
            if disc < 0:
                i_act = self.source_voltage / (2 * self.source_resistance)
            else:
                i_act = (self.source_voltage - math.sqrt(disc)) / (2 * self.source_resistance)

            v_act = self.source_voltage - i_act * self.source_resistance
            p_act = v_act * i_act

        if v_act > self._ovp_limit:
            self._protection_tripped = "OVP"
            self._input_enabled = False
            print(f"[SIM] PROTECTION TRIPPED: Over-Voltage Protection! Measured: {v_act:.3f}V > Limit: {self._ovp_limit}V")
            return self.source_voltage, 0.0, 0.0

        if i_act > self._ocp_limit:
            self._protection_tripped = "OCP"
            self._input_enabled = False
            print(f"[SIM] PROTECTION TRIPPED: Over-Current Protection! Measured: {i_act:.3f}A > Limit: {self._ocp_limit}A")
            return self.source_voltage, 0.0, 0.0

        if p_act > self._opp_limit:
            self._protection_tripped = "OPP"
            self._input_enabled = False
            print(f"[SIM] PROTECTION TRIPPED: Over-Power Protection! Measured: {p_act:.3f}W > Limit: {self._opp_limit}W")
            return self.source_voltage, 0.0, 0.0

        return v_act, i_act, p_act

    def measure_voltage(self) -> MeasurementResult:
        v_act, i_act, _ = self._update_physics()
        noise = random.uniform(-0.001, 0.001) * v_act if i_act != 0.0 else 0.0
        return MeasurementResult(v_act + noise, "V")

    def measure_current(self) -> MeasurementResult:
        _, i_act, _ = self._update_physics()
        noise = random.uniform(-0.001, 0.001) * i_act
        return MeasurementResult(i_act + noise, "A")

    def measure_power(self) -> MeasurementResult:
        _, _, p_act = self._update_physics()
        noise = random.uniform(-0.001, 0.001) * p_act
        return MeasurementResult(p_act + noise, "W")

    def shutdown_safety(self):
        self.set_input(False)
        self.sync_config()

class SimulatedDriver(SimulatedMultimeter):
    pass
