import json
import time
from typing import List
from .base import InstrumentDriver, SignalGenerator, SpectrumAnalyzer, NetworkAnalyzer, Oscilloscope, Multimeter, PowerSupply
from ..results import MeasurementResult

class SCPIPair:
    """Represents a single SCPI command/response transaction."""
    def __init__(self, command: str, response: str, timestamp: float = None):
        self.command = command
        self.response = response
        self.timestamp = timestamp or time.time()

    def to_dict(self):
        return {
            "cmd": self.command,
            "res": self.response,
            "ts": self.timestamp
        }

class GoldenMaster:
    """Handles saving and loading of SCPI transaction logs."""
    def __init__(self, filename: str):
        self.filename = filename
        self.transactions: List[SCPIPair] = []

    def add(self, command: str, response: str):
        self.transactions.append(SCPIPair(command, response))

    def save(self):
        with open(self.filename, 'w') as f:
            json.dump([t.to_dict() for t in self.transactions], f, indent=2)

    def load(self):
        with open(self.filename, 'r') as f:
            data = json.load(f)
            self.transactions = [SCPIPair(d['cmd'], d['res'], d['ts']) for d in data]

class RecordingWrapper:
    """Wraps an existing driver to record its SCPI traffic."""
    def __init__(self, driver: InstrumentDriver, master: GoldenMaster):
        self.driver = driver
        self.master = master
        
        # Monkey patch the driver's low-level methods
        self._original_write = driver.write
        self._original_query = driver.query
        
        driver.write = self.write
        driver.query = self.query

    def write(self, command: str):
        self._original_write(command)
        self.master.add(command, "")

    def query(self, command: str) -> str:
        response = self._original_query(command)
        self.master.add(command, response)
        return response

    def __getattr__(self, name):
        """Proxy all other calls to the original driver."""
        return getattr(self.driver, name)

class ReplayDriver(SignalGenerator, SpectrumAnalyzer, NetworkAnalyzer, Oscilloscope, Multimeter, PowerSupply):
    """An instrument driver that replays responses from a Golden Master file."""
    def __init__(self, resource_address: str, master_file: str):
        super().__init__(resource_address)
        self.master = GoldenMaster(master_file)
        self.master.load()
        self.ptr = 0

    def connect(self):
        print(f"[REPLAY] Loading master from {self.master.filename}")

    def disconnect(self):
        print("[REPLAY] Finished replay session")

    def write(self, command: str):
        if self.ptr < len(self.master.transactions):
            expected = self.master.transactions[self.ptr].command
            if command.strip().upper() == expected.strip().upper():
                self.ptr += 1
        else:
             pass

    def query(self, command: str) -> str:
        if self.ptr < len(self.master.transactions):
            tx = self.master.transactions[self.ptr]
            if command.strip().upper() == tx.command.strip().upper():
                self.ptr += 1
                return tx.response
        return "0"

    def safe_send(self, command: str):
        self.write(command)
        self.check_errors()

    def query_ascii(self, command: str) -> str:
        resp = self.query(command)
        self.check_errors()
        return resp

    def get_id(self): return self.query("*IDN?")
    def preset(self, automation_optimized=True): pass
    def clear_status(self): pass
    def sync_config(self): pass
    def wait_ready(self, timeout=30): pass
    def shutdown_safety(self): pass
    def check_errors(self): pass

    # --- Multimeter ---
    def configure_voltage_ac(self): self.write(":CONF:VOLT:AC")
    def configure_voltage_dc(self): self.write(":CONF:VOLT:DC")
    def set_auto_range(self, state: bool): self.write(f":VOLT:RANG:AUTO {'ON' if state else 'OFF'}")
    def measure_voltage(self, ac: bool = False): return MeasurementResult(float(self.query("MEAS:VOLT?")), "V")
    def measure_resistance(self, four_wire: bool = False): return MeasurementResult(float(self.query("MEAS:RES?")), "Ohm")
    def measure_current(self, ac: bool = False): return MeasurementResult(float(self.query("MEAS:CURR?")), "A")
    def measure_frequency(self): return MeasurementResult(float(self.query("MEAS:FREQ?")), "Hz")
    def measure_duty_cycle(self): return MeasurementResult(0.0, "%")
    def measure_v_peak_to_peak(self): return MeasurementResult(0.0, "V")

    # --- PowerSupply / FunctionGenerator Overlap ---
    def set_voltage(self, voltage: float): self.write(f":VOLT {voltage}")
    def get_voltage(self) -> float: return 0.0
    def set_current_limit(self, current: float): self.write(f":CURR {current}")
    def get_current(self) -> MeasurementResult: return MeasurementResult(0.0, "A")
    def set_output(self, state: bool): self.write(f":OUTP {'ON' if state else 'OFF'}")
    def get_output(self) -> bool: return False
    def set_ovp(self, voltage: float): self.write(f":VOLT:PROT {voltage}")
    def set_ocp(self, current: float): self.write(f":CURR:PROT {current}")
    def measure_voltage_actual(self) -> MeasurementResult: return MeasurementResult(0.0, "V")
    def clear_protection(self): self.write(":OUTP:PROT:CLE")

    # --- SpectrumAnalyzer / NetworkAnalyzer Overlap ---
    def peak_search(self): self.write(":CALC:MARK1:MAX")
    def get_marker_amplitude(self): return MeasurementResult(float(self.query("CALC:MARK1:Y?")), "dBm")
    def set_center_freq(self, hz: float): self.write(f":SENS:FREQ:CENT {hz}")
    def get_center_freq(self) -> float: return float(self.query(":SENS:FREQ:CENT?"))
    def set_span(self, hz: float): self.write(f":SENS:FREQ:SPAN {hz}")
    def get_span(self) -> float: return float(self.query(":SENS:FREQ:SPAN?"))
    def set_rbw(self, hz: float): self.write(f":SENS:BAND {hz}")
    def set_vbw(self, hz: float): self.write(f":SENS:BAND:VID {hz}")
    def get_trace_data(self, measurement_name: str = "CH1_S11_1") -> MeasurementResult: return MeasurementResult([0.0], "dB")

    # --- NetworkAnalyzer Specific ---
    def set_start_frequency(self, freq_hz: float): self.write(f"SENS:FREQ:STAR {freq_hz}")
    def set_stop_frequency(self, freq_hz: float): self.write(f"SENS:FREQ:STOP {freq_hz}")
    def set_points(self, num_points: int): self.write(f"SENS:SWE:POIN {num_points}")
    def set_parameter(self, parameter: str): self.write(f"CALC:PAR:MOD {parameter}")
    def get_complex_trace(self, measurement_name: str = "CH1_S11_1"): return MeasurementResult([complex(0,0)], "IQ")

    # --- Oscilloscope ---
    def run(self): self.write(":RUN")
    def stop(self): self.write(":STOP")
    def single(self): self.write(":SINGLE")
    def get_waveform(self, channel: int): return MeasurementResult([0.0], "V")
    def auto_scale(self): self.write(":AUT")
    def set_trigger(self, source, level, slope): self.write(":TRIG")
    def get_screenshot(self) -> bytes: return b""

    # --- SignalGenerator ---
    def set_frequency(self, hz: float): self.write(f":FREQ {hz}")
    def set_amplitude(self, dbm: float): self.write(f":POW {dbm}")
    def set_mod_state(self, mod_type: str, state: bool): self.write(f":{mod_type}:STAT {'ON' if state else 'OFF'}")
    def start_sweep(self, start: float, stop: float, points: int, dwell: float): self.write(":INIT")
    def configure_list_sweep(self, freq_list: List[float], power_list: List[float]): self.write(":LIST:FREQ")
    def set_reference_clock(self, source: str): self.write(f":ROSC:SOUR {source}")
    def set_offset(self, volts: float): self.write(f":VOLT:OFFS {volts}")
    def set_waveform(self, shape: str): self.write(f":FUNC {shape}")
