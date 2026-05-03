from .base import SignalGenerator, SpectrumAnalyzer
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult
from typing import List

@register_driver("SG")
class RohdeSchwarzSG(RealDriver, SignalGenerator):
    """Generic Driver for Rohde & Schwarz Signal Generators."""
    
    def __init__(self, resource: str):
        super().__init__(resource)
        self.min_frequency = 8e3
        self.max_frequency = 20e9
        self.max_power_dbm = 18.0

    def preset(self, automation_optimized: bool = True):
        self.write("*RST")
        if automation_optimized:
            self.write(":SYST:DISP:UPD OFF")
        self.sync_config()
        self.set_amplitude(-130.0)
        self.set_output(False)

    def shutdown_safety(self):
        self.set_output(False)
        self.set_amplitude(-130.0)
        self.sync_config()

    def set_frequency(self, hz: float):
        self.safe_send(f":FREQ {self.format_frequency(hz)}")

    def set_amplitude(self, dbm: float):
        self.safe_send(f":POW {self.format_power(dbm)}")

    def set_output(self, state: bool):
        self.write(f":OUTP {'ON' if state else 'OFF'}")

    def set_mod_state(self, mod_type: str, state: bool):
        mod_upper = mod_type.upper()
        state_str = 'ON' if state else 'OFF' # R&S standard
        if mod_upper == 'AM': self.safe_send(f":AM:STAT {state_str}")
        elif mod_upper == 'FM': self.safe_send(f":FM:STAT {state_str}")
        elif mod_upper in ['PULSE', 'PULM']: self.safe_send(f":PULM:STAT {state_str}")
        else: self._unsupported_feature(f"{mod_type} Modulation")

    def start_sweep(self, start: float, stop: float, points: int, dwell: float):
        self.set_output(True) # Ensure RF is ON for sweep
        self.safe_send(f":FREQ:STAR {start}")
        self.safe_send(f":FREQ:STOP {stop}")
        self.safe_send(f":SWE:POIN {points}")
        self.safe_send(f":SWE:DWEL {dwell}")
        self.safe_send(":FREQ:MODE SWE")
        self.write(":INIT")
        self.wait_ready()

    def configure_list_sweep(self, freq_list: List[float], power_list: List[float]):
        freq_str = ",".join([str(f) for f in freq_list])
        pow_str = ",".join([str(p) for p in power_list])
        self.safe_send(f":LIST:FREQ {freq_str}")
        self.safe_send(f":LIST:POW {pow_str}")
        self.safe_send(":FREQ:MODE LIST")

    def set_reference_clock(self, source: str):
        self.safe_send(f":ROSC:SOUR {source}")

@register_driver("SA")
class RohdeSchwarzSA(RealDriver, SpectrumAnalyzer):
    """Generic Driver for Rohde & Schwarz Spectrum Analyzers."""
    
    def preset(self, automation_optimized: bool = True):
        self.write("*RST")
        self.wait_ready()

    def peak_search(self):
        self.safe_send(":CALC:MARK1:MAX") 

    def get_marker_amplitude(self) -> MeasurementResult:
        val = self.query_ascii(":CALC:MARK1:Y?")
        return MeasurementResult(float(val), "dBm")

    def set_center_freq(self, hz: float):
        self.safe_send(f":FREQ:CENT {self.format_frequency(hz)}")

    def get_center_freq(self) -> float:
        return float(self.query(":FREQ:CENT?"))

    def set_span(self, hz: float):
        self.safe_send(f":FREQ:SPAN {self.format_frequency(hz)}")

    def get_span(self) -> float:
        return float(self.query(":FREQ:SPAN?"))

    def set_ref_level(self, dbm: float):
        self.write(f":DISP:WIND:TRAC:Y:RLEV {dbm}")

    def set_attenuation(self, db: float):
        self.write(f":SENS:POW:ATT {db}")

    def set_rbw(self, hz: float):
        self.safe_send(f":BAND {self.format_frequency(hz)}")

    def set_vbw(self, hz: float):
        self.safe_send(f":BAND:VID {self.format_frequency(hz)}")

    def get_trace_data(self) -> MeasurementResult:
        # Optimization: Use 32-bit float binary transfer with *WAI sync
        self.write(":FORM REAL,32")
        self.write(":INIT:CONT OFF")
        self.write(":INIT;*WAI") # Single sweep and wait
        data = self.query_binary_values(":TRAC:DATA? TRACE1", datatype='f', is_big_endian=False)
        self.write(":INIT:CONT ON")
        return MeasurementResult(list(data), "dBm")
