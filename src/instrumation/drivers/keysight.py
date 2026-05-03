from .base import SpectrumAnalyzer, NetworkAnalyzer, SignalGenerator
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult
from ..exceptions import ConfigurationError, OverloadError
from typing import List

@register_driver("SA")
class KeysightMXA(RealDriver, SpectrumAnalyzer):
    """Driver for Keysight MXA Series Spectrum Analyzers."""
    
    def preset(self, automation_optimized: bool = True):
        self.write("*RST")
        if automation_optimized:
            self.write(":DISP:ENAB OFF")
        self.wait_ready()
    def shutdown_safety(self):
        self.write(":DISP:ENAB ON")
        self.sync_config()

    def peak_search(self):
        self.write(":CALC:MARK1:STAT ON")
        self.write(":CALC:MARK1:TRAC 1")
        self.safe_send(":CALC:MARK1:MAX") 
        self.wait_ready()

    def get_marker_amplitude(self) -> MeasurementResult:
        val = self.query_ascii(":CALC:MARK1:Y?")
        return MeasurementResult(float(val), "dBm")

    def set_center_freq(self, hz: float):
        self._validate_frequency(hz)
        self.write(f":SENS:FREQ:CENT {hz}")

    def get_center_freq(self) -> float:
        return float(self.query(":SENS:FREQ:CENT?"))

    def set_span(self, hz: float):
        self.write(f":SENS:FREQ:SPAN {hz}")

    def get_span(self) -> float:
        return float(self.query(":SENS:FREQ:SPAN?"))

    def set_rbw(self, hz: float):
        self.safe_send(f":SENS:BAND {hz}")

    def set_vbw(self, hz: float):
        self.safe_send(f":SENS:BAND:VID {hz}")

    def get_trace_data(self) -> MeasurementResult:
        # Optimization: Use 32-bit float binary transfer instead of ASCII
        self.write(":FORM:DATA REAL,32")
        self.write(":FORM:BORD SWAP") # Ensure Little-Endian
        self.write(":INIT:CONT OFF")  # Single sweep mode
        self.write(":INIT:IMM")       # Trigger sweep
        self.wait_ready()             # Wait for sweep completion
        data = self.query_binary_values(":TRAC? TRACE1", datatype='f', is_big_endian=False)
        self.write(":INIT:CONT ON")   # Restore continuous sweep
        return MeasurementResult(list(data), "dBm")
    def measure_frequency(self) -> MeasurementResult: return MeasurementResult(0.0, "Hz")
    def measure_duty_cycle(self) -> MeasurementResult: return MeasurementResult(0.0, "%")
    def measure_v_peak_to_peak(self) -> MeasurementResult: return MeasurementResult(0.0, "V")

@register_driver("SA")
class KeysightPXA(KeysightMXA):
    """Driver for Keysight PXA Series Spectrum Analyzers (N9030A/B)."""
    def __init__(self, resource: str):
        super().__init__(resource)
        # PXA typically has higher performance and frequency range
        self.max_frequency = 50e9 

@register_driver("NA")
class KeysightPNA(RealDriver, NetworkAnalyzer):
    """Driver for Keysight PNA Series."""
    def preset(self, automation_optimized: bool = True):
        self.write("*RST")
        self.wait_ready()

    def set_start_frequency(self, freq_hz: float):
        self.safe_send(f"SENS:FREQ:STAR {freq_hz}")

    def set_stop_frequency(self, freq_hz: float):
        self.safe_send(f"SENS:FREQ:STOP {freq_hz}")

    def set_points(self, num_points: int):
        self.safe_send(f"SENS:SWE:POIN {num_points}")

    def get_trace_data(self, measurement_name: str) -> MeasurementResult:
        self.safe_send(f"CALC:PAR:SEL '{measurement_name}'")
        self.write("FORM:DATA REAL,32")
        data = self.query_binary_values("CALC:DATA? FDATA", datatype='f', is_big_endian=False)
        return MeasurementResult(list(data), "dB")

    def get_complex_trace(self, measurement_name: str) -> MeasurementResult:
        self.safe_send(f"CALC:PAR:SEL '{measurement_name}'")
        self.write("FORM:DATA REAL,32")
        raw_data = self.query_binary_values("CALC:DATA? SDATA", datatype='f', is_big_endian=False)
        data = [complex(raw_data[i], raw_data[i+1]) for i in range(0, len(raw_data), 2)]
        return MeasurementResult(data, "IQ")

    def measure_frequency(self) -> MeasurementResult: return MeasurementResult(0.0, "Hz")
    def measure_duty_cycle(self) -> MeasurementResult: return MeasurementResult(0.0, "%")
    def measure_v_peak_to_peak(self) -> MeasurementResult: return MeasurementResult(0.0, "V")

@register_driver("SG")
class KeysightSG(RealDriver, SignalGenerator):
    """Driver for Keysight Signal Generators (EXG/MXG)."""
    
    def __init__(self, resource: str):
        super().__init__(resource)
        self.min_frequency = 9e3
        self.max_frequency = 6e9
        self.max_power_dbm = 10.0

    def preset(self, automation_optimized: bool = True):
        self.write("*RST")
        if automation_optimized:
            self.write(":DISP:STAT OFF")
        self.sync_config()
        self.set_amplitude(-130.0)
        self.set_output(False)

    def shutdown_safety(self):
        """Emergency Shutdown: RF OFF and -130 dBm, then restore Display."""
        self.set_output(False)
        self.set_amplitude(-130.0)
        self.write(":DISP:STAT ON")
        self.sync_config()

    def set_frequency(self, hz: float):
        self.safe_send(f":FREQ {self.format_frequency(hz)}")

    def set_amplitude(self, dbm: float):
        self.safe_send(f":POW {self.format_power(dbm)}")

    def set_output(self, state: bool):
        self.write(f":OUTP {'ON' if state else 'OFF'}")

    def set_mod_state(self, mod_type: str, state: bool):
        mod_upper = mod_type.upper()
        state_str = 'ON' if state else 'OFF'
        if mod_upper == 'AM': self.safe_send(f":AM:STAT {state_str}")
        elif mod_upper == 'FM': self.safe_send(f":FM:STAT {state_str}")
        elif mod_upper == 'PULSE': self.safe_send(f":PULM:STAT {state_str}")
        else: self._unsupported_feature(f"{mod_type} Modulation")

    def start_sweep(self, start: float, stop: float, points: int, dwell: float):
        self.safe_send(f":FREQ:STAR {self.format_frequency(start)}")
        self.safe_send(f":FREQ:STOP {self.format_frequency(stop)}")
        self.safe_send(f":SWE:POIN {points}")
        self.safe_send(f":SWE:DWEL {dwell}")
        self.safe_send(":FREQ:MODE LIST")
        self.write(":INIT:CONT OFF")
        self.write(":INIT")
        self.wait_ready()

    def configure_list_sweep(self, freq_list: List[float], power_list: List[float]):
        freq_str = ",".join([str(f) for f in freq_list])
        pow_str = ",".join([str(p) for p in power_list])
        self.safe_send(f":LIST:FREQ {freq_str}")
        self.safe_send(f":LIST:POW {pow_str}")

    def set_reference_clock(self, source: str):
        self.safe_send(f":ROSC:SOUR {source}")

    def measure_frequency(self) -> MeasurementResult: return MeasurementResult(0.0, "Hz")
    def measure_duty_cycle(self) -> MeasurementResult: return MeasurementResult(0.0, "%")
    def measure_v_peak_to_peak(self) -> MeasurementResult: return MeasurementResult(0.0, "V")
@register_driver("COMBO_VNA_SA")
class KeysightFieldFox(RealDriver, SpectrumAnalyzer, NetworkAnalyzer):
    """
    Driver for Keysight FieldFox N99xx Series.
    Multi-mode instrument - SA and NA modes share this driver.
    Uses automatic mode-switching via :INST:SEL.
    """

    MODES = {"SA": "SA", "VNA": "NA", "CAT": "CAT", "PM": "POW"}

    def _set_mode(self, mode_key: str):
        target = self.MODES.get(mode_key.upper(), mode_key)
        current = self.query(":INST:SEL?").strip().strip('"')
        if current != target:
            self.write(f":INST:SEL {target}")
            self.wait_ready()

    def preset(self, automation_optimized: bool = True):
        self.write("*RST")
        self.wait_ready()

    # SA Interface
    def set_center_freq(self, hz: float):
        self._set_mode("SA")
        self.write(f":SENS:FREQ:CENT {hz}")

    def get_center_freq(self) -> float:
        self._set_mode("SA")
        return float(self.query(":SENS:FREQ:CENT?"))

    def set_span(self, hz: float):
        self._set_mode("SA")
        self.write(f":SENS:FREQ:SPAN {hz}")

    def get_span(self) -> float:
        self._set_mode("SA")
        return float(self.query(":SENS:FREQ:SPAN?"))

    def get_trace_data(self, measurement_name: str = "TRACE1") -> MeasurementResult:
        # Check current mode to decide which tree to use
        current_mode = self.query(":INST:SEL?").strip().strip('"')
        
        if current_mode == "SA":
            self.write(":FORM:DATA REAL,32")
            data = self.query_binary_values(":TRAC? TRACE1", datatype='f', is_big_endian=False)
            return MeasurementResult(list(data), "dBm")
        else:
            # PNA/VNA mode fetch
            self.write("FORM:DATA REAL,32")
            data = self.query_binary_values("CALC:DATA? FDATA", datatype='f', is_big_endian=False)
            return MeasurementResult(list(data), "dB")

    # VNA Interface
    def set_start_frequency(self, freq_hz: float):
        self._set_mode("VNA")
        self.write(f":SENS:FREQ:STAR {freq_hz}")

    def get_complex_trace(self, measurement_name: str = "S11") -> MeasurementResult:
        self._set_mode("VNA")
        self.write(":FORM:DATA REAL,32")
        raw_data = self.query_binary_values("CALC:DATA? SDATA", datatype='f', is_big_endian=False)
        data = [complex(raw_data[i], raw_data[i+1]) for i in range(0, len(raw_data), 2)]
        return MeasurementResult(data, "IQ")

    def shutdown_safety(self):
        self.sync_config()
