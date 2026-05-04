from abc import ABC, abstractmethod
from typing import List, Union, Dict
import asyncio
from ..results import MeasurementResult
from ..exceptions import OverloadError, ConfigurationError

class InstrumentDriver(ABC):
    """Abstract Base Class for all instrument drivers following the 'Abstract Hardware' spec."""
    def __init__(self, resource: str):
        self.resource = resource
        self.connected = False
        self.is_simulated = False
        
        # Identity & Capabilities
        self.identity: Dict[str, str] = {"manufacturer": "", "model": "", "serial": "", "version": ""}
        self.options: List[str] = []
        self.error_stack: List[str] = []
        
        # Software Safety Guardrails
        self.min_frequency = 0.0
        self.max_frequency = 1e12
        self.max_power_dbm = 0.0
        self.max_voltage = 0.0

    def __getattr__(self, name: str):
        """Dynamic async wrapper for all driver methods."""
        if name.startswith("async_"):
            sync_name = name[6:]
            if hasattr(self, sync_name):
                sync_method = getattr(self, sync_name)
                async def wrapper(*args, **kwargs):
                    return await asyncio.to_thread(sync_method, *args, **kwargs)
                return wrapper
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


    @property
    def resource_address(self) -> str:
        return self.resource

    @abstractmethod
    def connect(self):
        """Establishes connection and performs identity/option discovery."""
        pass

    @abstractmethod
    def disconnect(self):
        """Safely tears down connection."""
        pass

    def close(self):
        self.disconnect()

    @abstractmethod
    def write(self, command: str): pass

    @abstractmethod
    def query(self, command: str) -> str: pass

    def safe_send(self, command: str):
        """Sends command and immediately checks SYST:ERR?."""
        raise NotImplementedError()

    def query_ascii(self, command: str) -> str:
        """Sends command, reads response, and checks for errors."""
        raise NotImplementedError()

    def query_binary_values(self, command: str, datatype: str = 'f', is_big_endian: bool = False) -> List[float]:
        """High-speed binary data transfer."""
        raise NotImplementedError()

    @abstractmethod
    def get_id(self) -> str: pass

    # --- Global Logic & Synchronization ---
    @abstractmethod
    def preset(self, automation_optimized: bool = True): pass

    @abstractmethod
    def clear_status(self):
        """Executes *CLS."""
        pass

    @abstractmethod
    def sync_config(self):
        """Executes *CLS and *WAI for a clean slate."""
        pass

    @abstractmethod
    def wait_ready(self, timeout: float = 30.0):
        """Standard polling loop for *OPC?."""
        pass

    @abstractmethod
    def shutdown_safety(self):
        """Emergency shutdown protocol (Outputs OFF, Power/Volt 0)."""
        pass

    @abstractmethod
    def check_errors(self):
        """Queries SYST:ERR? and updates local error_stack."""
        pass

    def save_state(self, index: Union[int, str]):
        """Saves current state to memory."""
        self._unsupported_feature("save_state")

    def load_state(self, index: Union[int, str]):
        """Recalls state from memory."""
        self._unsupported_feature("load_state")

    # --- Unit Guards & Formatting ---
    def format_frequency(self, val: Union[float, str]) -> str:
        """Ensures input is Hz and formats for SCPI (e.g. 1.5e9 -> '1.5 GHz')."""
        hz = float(val)
        self._validate_frequency(hz)
        if hz >= 1e9:
            return f"{hz/1e9:.6f} GHz"
        if hz >= 1e6:
            return f"{hz/1e6:.6f} MHz"
        if hz >= 1e3:
            return f"{hz/1e3:.6f} kHz"
        return f"{hz:.0f} Hz"

    def format_power(self, dbm: float) -> str:
        self._validate_power(dbm)
        return f"{dbm:.2f} DBM"

    def _unsupported_feature(self, feature_name: str):
        print(f"Warning: Feature '{feature_name}' is not supported by {self.identity.get('model', 'Instrument')}")

    def _validate_frequency(self, hz: float):
        if hz < self.min_frequency or hz > self.max_frequency:
            raise ConfigurationError(f"Frequency {hz} Hz out of safety range")

    def _validate_power(self, dbm: float):
        if dbm > self.max_power_dbm:
            raise OverloadError(f"Power {dbm} dBm exceeds safety limit")

    # --- Measurements ---
    @abstractmethod
    def measure_frequency(self) -> MeasurementResult: pass
    @abstractmethod
    def measure_duty_cycle(self) -> MeasurementResult: pass
    @abstractmethod
    def measure_v_peak_to_peak(self) -> MeasurementResult: pass

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.shutdown_safety()
        except Exception:
            pass
        self.disconnect()

class Multimeter(InstrumentDriver):
    @abstractmethod
    def configure_voltage_dc(self): pass
    @abstractmethod
    def configure_voltage_ac(self): pass
    @abstractmethod
    def measure_voltage(self, ac: bool = False) -> MeasurementResult: pass
    @abstractmethod
    def measure_resistance(self, four_wire: bool = False) -> MeasurementResult: pass
    @abstractmethod
    def measure_current(self, ac: bool = False) -> MeasurementResult: pass
    @abstractmethod
    def set_auto_range(self, state: bool): pass

class PowerSupply(InstrumentDriver):
    @abstractmethod
    def set_voltage(self, voltage: float): pass
    @abstractmethod
    def get_voltage(self) -> float: pass
    @abstractmethod
    def set_current_limit(self, current: float): pass
    def set_current(self, current: float):
        """Generalized alias for set_current_limit."""
        self.set_current_limit(current)
    @abstractmethod
    def get_current(self) -> MeasurementResult: pass
    @abstractmethod
    def set_output(self, state: bool): pass
    @abstractmethod
    def get_output(self) -> bool: pass
    @abstractmethod
    def set_ovp(self, voltage: float): pass
    @abstractmethod
    def set_ocp(self, current: float): pass
    @abstractmethod
    def measure_voltage_actual(self) -> MeasurementResult: pass
    @abstractmethod
    def measure_current(self) -> MeasurementResult: pass

    def set_voltage_limit(self, voltage: float):
        """Generalized alias for Over-Voltage Protection (OVP)."""
        self.set_ovp(voltage)

    def measure_voltage(self) -> MeasurementResult:
        """Generalized alias for measure_voltage_actual."""
        return self.measure_voltage_actual()

    @abstractmethod
    def clear_protection(self): pass

    def measure_power(self) -> MeasurementResult:
        """Queries the actual measured output power (Watts)."""
        self._unsupported_feature("measure_power")
        return MeasurementResult(0.0, "W")

    def set_foldback_mode(self, mode: str):
        """Sets the foldback protection mode (OFF, CC, or CV)."""
        self._unsupported_feature("set_foldback_mode")

    def set_foldback_delay(self, seconds: float):
        """Sets the delay for foldback protection."""
        self._unsupported_feature("set_foldback_delay")

    def set_autostart(self, state: bool):
        """Sets the Power-ON state (SAFE/OFF or AUTO/ON)."""
        self._unsupported_feature("set_autostart")

    def get_mode(self) -> str:
        """Returns the current operation mode (CV, CC, or OFF)."""
        self._unsupported_feature("get_mode")
        return "OFF"

class SpectrumAnalyzer(InstrumentDriver):
    @abstractmethod
    def peak_search(self): pass
    @abstractmethod
    def get_marker_amplitude(self) -> MeasurementResult: pass
    @abstractmethod
    def set_center_freq(self, hz: float): pass
    @abstractmethod
    def get_center_freq(self) -> float: pass
    @abstractmethod
    def set_span(self, hz: float): pass
    @abstractmethod
    def get_span(self) -> float: pass
    @abstractmethod
    def set_rbw(self, hz: float): pass
    @abstractmethod
    def set_vbw(self, hz: float): pass
    @abstractmethod
    def get_trace_data(self) -> MeasurementResult: pass

    def get_peak_value(self) -> MeasurementResult:
        """Helper: Performs peak search and returns marker amplitude."""
        self.peak_search()
        return self.get_marker_amplitude()

class NetworkAnalyzer(InstrumentDriver):
    @abstractmethod
    def set_start_frequency(self, freq_hz: float): pass
    @abstractmethod
    def set_stop_frequency(self, freq_hz: float): pass
    
    def set_center_freq(self, freq_hz: float): 
        self._unsupported_feature("set_center_freq")

    def set_center_frequency(self, freq_hz: float):
        """Alias for set_center_freq."""
        self.set_center_freq(freq_hz)
    
    def set_span(self, span_hz: float): 
        self._unsupported_feature("set_span")
    
    @abstractmethod
    def set_points(self, num_points: int): pass
    
    def set_if_bandwidth(self, hz: float): 
        self._unsupported_feature("set_if_bandwidth")
    
    def set_power_level(self, dbm: float): 
        self._unsupported_feature("set_power_level")
    
    def set_sweep_type(self, sweep_type: str): 
        self._unsupported_feature("set_sweep_type")
    
    def set_averaging(self, state: bool, count: int = 10): 
        self._unsupported_feature("set_averaging")
    
    def set_continuous(self, state: bool): 
        self._unsupported_feature("set_continuous")
    
    @abstractmethod
    def set_parameter(self, parameter: str): pass  # e.g., "S11", "S21"
    
    @abstractmethod
    def get_trace_data(self, measurement_name: str = "CH1_S11_1") -> MeasurementResult: pass
    
    @abstractmethod
    def get_complex_trace(self, measurement_name: str = "CH1_S11_1") -> MeasurementResult: pass
    
    @abstractmethod
    def get_smith_data(self, measurement_name: str = "CH1_S11_1") -> MeasurementResult: pass
    
    def peak_search(self, marker: int = 1): 
        self._unsupported_feature("peak_search")
    
    def get_marker_x(self, marker: int = 1) -> float: 
        self._unsupported_feature("get_marker_x")
        return 0.0
    
    def get_marker_y(self, marker: int = 1) -> float: 
        self._unsupported_feature("get_marker_y")
        return 0.0
    
    def save_state(self, filename: str): 
        self._unsupported_feature("save_state")
    
    def load_state(self, filename: str): 
        self._unsupported_feature("load_state")

    def wait_for_sweep(self):
        """Wait for the current sweep to complete."""
        self._unsupported_feature("wait_for_sweep")

class Oscilloscope(InstrumentDriver):
    @abstractmethod
    def run(self): pass
    @abstractmethod
    def stop(self): pass
    @abstractmethod
    def single(self): pass
    @abstractmethod
    def get_waveform(self, channel: int) -> MeasurementResult: pass
    @abstractmethod
    def auto_scale(self): pass
    @abstractmethod
    def set_trigger(self, source: str, level: float, slope: str): pass
    @abstractmethod
    def get_screenshot(self) -> bytes: pass

class SignalGenerator(InstrumentDriver):
    @abstractmethod
    def set_frequency(self, hz: float): pass
    @abstractmethod
    def set_amplitude(self, dbm: float): pass
    @abstractmethod
    def set_output(self, state: bool): pass
    @abstractmethod
    def set_mod_state(self, mod_type: str, state: bool): pass
    @abstractmethod
    def start_sweep(self, start: float, stop: float, points: int, dwell: float): pass
    @abstractmethod
    def configure_list_sweep(self, freq_list: List[float], power_list: List[float]): pass
    @abstractmethod
    def set_reference_clock(self, source: str): pass

class FunctionGenerator(SignalGenerator):
    """Specific for AFGs which use Volts/Waveforms instead of just dBm."""
    @abstractmethod
    def set_voltage(self, vpp: float): pass
    @abstractmethod
    def set_offset(self, volts: float): pass
    @abstractmethod
    def set_waveform(self, shape: str): pass # SIN, SQU, PULS, RAMP, NOIS, DC
