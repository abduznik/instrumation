from .base import SpectrumAnalyzer, NetworkAnalyzer
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult

@register_driver("SA")
class AnritsuSA(RealDriver, SpectrumAnalyzer):
    """Generic Driver for Anritsu Spectrum Analyzers."""
    
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
        # Optimization: Use 32-bit float binary transfer
        self.write(":FORM:DATA REAL32")
        data = self.query_binary_values(":TRAC:DATA? TRACE1", datatype='f', is_big_endian=False)
        return MeasurementResult(list(data), "dBm")

    def shutdown_safety(self):
        self.sync_config()

@register_driver("NA")
class AnritsuVNA(RealDriver, NetworkAnalyzer):
    """Generic Driver for Anritsu Vector Network Analyzers (Handheld/Legacy)."""
    
    def preset(self, automation_optimized: bool = True):
        self.write("*RST")
        self.wait_ready()

    def set_start_frequency(self, freq_hz: float):
        self.safe_send(f":SENS:FREQ:STAR {freq_hz}")

    def set_stop_frequency(self, freq_hz: float):
        self.safe_send(f":SENS:FREQ:STOP {freq_hz}")

    def set_points(self, num_points: int):
        self.safe_send(f":SENS:SWE:POIN {num_points}")

    def set_parameter(self, parameter: str):
        self.safe_send(f":CALC:PAR:SEL '{parameter}'")

    def get_trace_data(self, measurement_name: str = "S11") -> MeasurementResult:
        self.safe_send(f":CALC:PAR:SEL '{measurement_name}'")
        self.write(":FORM REAL")
        data = self.query_binary_values(":CALC:DATA? FDATA", datatype='f', is_big_endian=False)
        return MeasurementResult(list(data), "dB")

    def get_complex_trace(self, measurement_name: str = "S11") -> MeasurementResult:
        self.safe_send(f":CALC:PAR:SEL '{measurement_name}'")
        self.write(":FORM REAL")
        raw_data = self.query_binary_values(":CALC:DATA? SDATA", datatype='f', is_big_endian=False)
        data = [complex(raw_data[i], raw_data[i+1]) for i in range(0, len(raw_data), 2)]
        return MeasurementResult(data, "IQ")

    def get_smith_data(self, measurement_name: str = "S11") -> MeasurementResult:
        self._unsupported_feature("get_smith_data")
        return MeasurementResult([], "Z")

@register_driver("NA")
class AnritsuShockLineVNA(RealDriver, NetworkAnalyzer):
    """Driver for Anritsu ShockLine MS46522B/MS46524B VNAs."""

    def connect(self):
        super().connect()
        self._discover_capabilities()

    def _discover_capabilities(self):
        try:
            self.min_frequency = float(self.query(":SENS1:FREQ:STAR? MIN"))
            self.max_frequency = float(self.query(":SENS1:FREQ:STOP? MAX"))
        except Exception:
            pass

    def preset(self, automation_optimized: bool = True):
        self.write("*RST")
        self.wait_ready()
        if automation_optimized:
            self.write(":SYSTem:DISPlay:UPDate OFF")

    def set_start_frequency(self, freq_hz: float):
        self.write(f":SENSe1:FREQuency:STARt {freq_hz}")

    def set_stop_frequency(self, freq_hz: float):
        self.write(f":SENSe1:FREQuency:STOP {freq_hz}")

    def set_points(self, num_points: int):
        self.write(f":SENSe1:SWEep:POINts {num_points}")

    def set_if_bandwidth(self, hz: float):
        self.write(f":SENSe1:BANDwidth:RESolution {hz}")

    def set_parameter(self, parameter: str):
        self.write(f":CALCulate1:PARameter:SELect '{parameter}'")

    def get_trace_data(self, measurement_name: str = "S21") -> MeasurementResult:
        self.write(f":CALCulate1:PARameter:SELect '{measurement_name}'")
        self.write(":FORMat:DATA REAL,32")
        self.write(":FORMat:BORDer SWAP") 
        self.write(":SENSe1:SWEep:MODE SINGle")
        self.wait_ready()
        data = self.query_binary_values(
            ":CALCulate1:DATA:FDATa?", datatype='f', is_big_endian=False
        )
        return MeasurementResult(list(data), "dB")

    def get_complex_trace(self, measurement_name: str = "S21") -> MeasurementResult:
        self.write(f":CALCulate1:PARameter:SELect '{measurement_name}'")
        self.write(":FORMat:DATA REAL,32")
        self.write(":FORMat:BORDer SWAP")
        self.write(":SENSe1:SWEep:MODE SINGle")
        self.wait_ready()
        raw = self.query_binary_values(
            ":CALCulate1:DATA:SDATa?", datatype='f', is_big_endian=False
        )
        data = [complex(raw[i], raw[i+1]) for i in range(0, len(raw), 2)]
        return MeasurementResult(data, "IQ")

    def get_smith_data(self, measurement_name: str = "S21") -> MeasurementResult:
        self._unsupported_feature("get_smith_data")
        return MeasurementResult([], "Z")

    def shutdown_safety(self):
        self.write(":SYSTem:DISPlay:UPDate ON")
        self.sync_config()

@register_driver("COMBO_VNA_SA")
class AnritsuMS2035B(RealDriver, SpectrumAnalyzer, NetworkAnalyzer):
    """Driver for Anritsu MS2035B VNA Master + Spectrum Analyzer combo."""

    VNA_MODE = "VNA"
    SA_MODE  = "SPA" # Spectrum Analyzer mode is usually SPA in handhelds

    def _set_mode(self, mode: str):
        current = self.query(":INSTrument:SELect?").strip().strip('"')
        if current != mode:
            self.write(f":INSTrument:SELect {mode}")
            self.wait_ready()

    # SA interface
    def set_center_freq(self, hz: float):
        self._set_mode(self.SA_MODE)
        self.safe_send(f":FREQ:CENT {hz}")

    def get_center_freq(self) -> float:
        self._set_mode(self.SA_MODE)
        return float(self.query(":FREQ:CENT?"))

    def set_span(self, hz: float):
        self._set_mode(self.SA_MODE)
        self.safe_send(f":FREQ:SPAN {hz}")

    def get_span(self) -> float:
        self._set_mode(self.SA_MODE)
        return float(self.query(":FREQ:SPAN?"))

    def get_trace_data(self, measurement_name: str = "TRACE1") -> MeasurementResult:
        # Check if we are in VNA mode or SA mode
        mode = self.query(":INSTrument:SELect?").strip().strip('"')
        if mode == self.SA_MODE:
            self.write(":FORM REAL")
            data = self.query_binary_values(":TRAC? TRACE1", datatype='f', is_big_endian=False)
            return MeasurementResult(list(data), "dBm")
        else:
            # VNA data fetch logic
            self.safe_send(f":CALC:PAR:SEL '{measurement_name}'")
            self.write(":FORM REAL")
            data = self.query_binary_values(":CALC:DATA? FDATA", datatype='f', is_big_endian=False)
            return MeasurementResult(list(data), "dB")

    def get_complex_trace(self, measurement_name: str = "S11") -> MeasurementResult:
        self._set_mode(self.VNA_MODE)
        self.safe_send(f":CALC:PAR:SEL '{measurement_name}'")
        self.write(":FORM REAL")
        raw_data = self.query_binary_values(":CALC:DATA? SDATA", datatype='f', is_big_endian=False)
        data = [complex(raw_data[i], raw_data[i+1]) for i in range(0, len(raw_data), 2)]
        return MeasurementResult(data, "IQ")

    def set_start_frequency(self, freq_hz: float):
        self._set_mode(self.VNA_MODE)
        self.write(f":SENS:FREQ:STAR {freq_hz}")

    def set_stop_frequency(self, freq_hz: float):
        self._set_mode(self.VNA_MODE)
        self.write(f":SENS:FREQ:STOP {freq_hz}")

    def set_points(self, num_points: int):
        self._set_mode(self.VNA_MODE)
        self.write(f":SENS:SWE:POIN {num_points}")

    def set_parameter(self, parameter: str):
        self._set_mode(self.VNA_MODE)
        self.write(f":CALC:PAR:SEL '{parameter}'")

    def get_smith_data(self, measurement_name: str = "S11") -> MeasurementResult:
        self._unsupported_feature("get_smith_data")
        return MeasurementResult([], "Z")

    def preset(self, automation_optimized: bool = True):
        self.write("*RST")
        self.wait_ready()
