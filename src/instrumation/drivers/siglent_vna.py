from typing import List
from .base import NetworkAnalyzer
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("VNA")
@register_driver("NA")
class SiglentSNA5000A(RealDriver, NetworkAnalyzer):
    """Driver for Siglent SNA5000A/X Series Vector Network Analyzers.

    Standard SCPI-99 network-analyzer subsystem, the same command
    shape as ``KeysightPNA`` -- Siglent's SNA5000A documentation is
    explicitly SCPI-99 compliant for this measurement class.

    SCPI Reference (SNA5000A Series Programming Guide):
        - SENSe:FREQuency:STARt/:STOP/:CENTer/:SPAN <hz>
        - SENSe:SWEep:POINts <n>
        - SENSe:BANDwidth <hz>
        - SOURce:POWer <dbm>
        - SENSe:SWEep:TYPE {LINear|LOGarithmic|SEGMent|POWer|CW}
        - SENSe:AVERage[:STATe] {ON|OFF} / :COUNt <n>
        - INITiate:CONTinuous {ON|OFF}
        - CALCulate:PARameter:DEFine:EXT '<name>','<param>'
        - CALCulate:PARameter:SELect '<name>'
        - CALCulate:DATA? FDATA / SDATA
        - CALCulate:MARKer<n>:FUNCtion:EXECute
    """

    def preset(self, automation_optimized: bool = True) -> None:
        self.write("*RST")
        self.wait_ready()

    def set_start_frequency(self, freq_hz: float) -> None:
        self.safe_send(f"SENS:FREQ:STAR {freq_hz}")

    def set_stop_frequency(self, freq_hz: float) -> None:
        self.safe_send(f"SENS:FREQ:STOP {freq_hz}")

    def set_center_frequency(self, freq_hz: float) -> None:
        self.safe_send(f"SENS:FREQ:CENT {freq_hz}")

    def set_span(self, span_hz: float) -> None:
        self.safe_send(f"SENS:FREQ:SPAN {span_hz}")

    def set_points(self, num_points: int) -> None:
        self.safe_send(f"SENS:SWE:POIN {num_points}")

    def set_if_bandwidth(self, hz: float) -> None:
        self.safe_send(f"SENS:BAND {hz}")

    def set_power_level(self, dbm: float) -> None:
        self.safe_send(f"SOUR:POW {dbm}")

    def set_sweep_type(self, sweep_type: str) -> None:
        self.safe_send(f"SENS:SWE:TYPE {sweep_type}")

    def set_averaging(self, state: bool, count: int = 10) -> None:
        self.safe_send(f"SENS:AVER {'ON' if state else 'OFF'}")
        self.safe_send(f"SENS:AVER:COUN {count}")

    def set_continuous(self, state: bool) -> None:
        self.write(f"INIT:CONT {'ON' if state else 'OFF'}")

    def set_parameter(self, parameter: str, measurement_name: str = "CH1_S11_1") -> None:
        self.safe_send(f"CALC:PAR:SEL '{measurement_name}'")
        self.safe_send(f"CALC:PAR:MOD {parameter}")

    def create_measurement(self, name: str, parameter: str, window: int = 1, trace: int = 1) -> None:
        self.safe_send(f"DISP:WIND{window}:STAT ON")
        self.safe_send(f"CALC:PAR:DEF:EXT '{name}','{parameter}'")
        self.safe_send(f"DISP:WIND{window}:TRAC{trace}:FEED '{name}'")

    def get_trace_data(self, measurement_name: str = "CH1_S11_1") -> MeasurementResult:
        self.safe_send(f"CALC:PAR:SEL '{measurement_name}'")
        data = self.query_binary_values("CALC:DATA? FDATA", datatype='f', is_big_endian=False)
        return MeasurementResult(list(data), "dB")

    def get_complex_trace(self, measurement_name: str = "CH1_S11_1") -> MeasurementResult:
        self.safe_send(f"CALC:PAR:SEL '{measurement_name}'")
        raw_data = self.query_binary_values("CALC:DATA? SDATA", datatype='f', is_big_endian=False)
        data = [complex(raw_data[i], raw_data[i + 1]) for i in range(0, len(raw_data), 2)]
        return MeasurementResult(data, "IQ")

    def get_smith_data(self, measurement_name: str = "CH1_S11_1") -> MeasurementResult:
        self.safe_send(f"CALC:PAR:SEL '{measurement_name}'")
        self.write("CALC:FORM SMITH")
        raw_data = self.query_binary_values("CALC:DATA? FDATA", datatype='f', is_big_endian=False)
        data = [complex(raw_data[i], raw_data[i + 1]) for i in range(0, len(raw_data), 2)]
        return MeasurementResult(data, "Z")

    def peak_search(self, marker: int = 1) -> None:
        self.write(f"CALC:MARK{marker}:STAT ON")
        self.write(f"CALC:MARK{marker}:FUNC:SEL MAX")
        self.write(f"CALC:MARK{marker}:FUNC:EXEC")

    def get_marker_x(self, marker: int = 1) -> float:
        return float(self.query(f"CALC:MARK{marker}:X?"))

    def get_marker_y(self, marker: int = 1) -> float:
        val = self.query(f"CALC:MARK{marker}:Y?")
        return float(val.split(',')[0])

    def save_state(self, filename: str) -> None:
        if not filename.endswith(".sta"):
            filename += ".sta"
        self.write(f"MMEM:STOR:STAT '{filename}'")

    def load_state(self, filename: str) -> None:
        if not filename.endswith(".sta"):
            filename += ".sta"
        self.write(f"MMEM:LOAD:STAT '{filename}'")

    def wait_for_sweep(self) -> None:
        self.query("*OPC?")
