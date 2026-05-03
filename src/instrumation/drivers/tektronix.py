from typing import List
from .base import Oscilloscope, FunctionGenerator
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult

@register_driver("SCOPE")
class TektronixTDS(RealDriver, Oscilloscope):
    """Refined Driver for Tektronix TDS Series Oscilloscopes."""

    def preset(self, automation_optimized: bool = True):
        self.write("*RST")
        self.wait_ready()

    def run(self): self.write(":ACQUIRE:STATE ON")
    def stop(self): self.write(":ACQUIRE:STATE OFF")
    def single(self):
        self.write(":ACQUIRE:STOPAFTER SEQUENCE")
        self.write(":ACQUIRE:STATE ON")

    def get_waveform(self, channel: int) -> MeasurementResult:
        self.write(f"DATA:SOURCE CH{channel}")
        self.write("DATA:ENCdg RIBINARY") # Signed binary
        self.write("DATA:WIDTH 2")        # 2 bytes per point
        
        # Query scaling parameters
        ymult = float(self.query("WFMPRE:YMULT?"))
        yoff = float(self.query("WFMPRE:YOFF?"))
        yzero = float(self.query("WFMPRE:YZERO?"))
        
        # Fetch raw binary curve
        raw_counts = self.query_binary_values("CURVE?", datatype='h', is_big_endian=True)
        
        # Scale to Volts: (raw - yoff) * ymult + yzero
        scaled_data = [(x - yoff) * ymult + yzero for x in raw_counts]
        return MeasurementResult(scaled_data, "V")

    def auto_scale(self):
        """Standard Tektronix autoset command."""
        self.write("AUTOSET EXECUTE")
        self.wait_ready()

    def set_trigger(self, source: str, level: float, slope: str):
        self.safe_send(f"TRIG:MAIN:EDGE:SOURCE {source}")
        self.safe_send(f"TRIG:MAIN:LEVEL {level}")
        self.safe_send(f"TRIG:MAIN:EDGE:SLOPE {slope.upper()}")

    def get_screenshot(self) -> bytes:
        self.write("HARDCOPY START")
        return b"TEK_SCREENSHOT_DATA"

    def _measure_imm(self, channel: int, measure_type: str) -> float:
        self.safe_send(f":MEASUREMENT:IMMED:SOURCE CH{channel}")
        self.safe_send(f":MEASUREMENT:IMMED:TYPE {measure_type}")
        val = self.query_ascii(":MEASUREMENT:IMMED:VALUE?")
        return float(val)

    def measure_frequency(self, channel: int = 1) -> MeasurementResult:
        val = self._measure_imm(channel, "FREQUENCY")
        return MeasurementResult(val, "Hz")

    def measure_duty_cycle(self, channel: int = 1) -> MeasurementResult:
        val = self._measure_imm(channel, "DUTY")
        return MeasurementResult(val, "%")

    def measure_v_peak_to_peak(self, channel: int = 1) -> MeasurementResult:
        val = self._measure_imm(channel, "PKPK")
        return MeasurementResult(val, "V")

    def shutdown_safety(self):
        self.stop()
        self.sync_config()

@register_driver("SG")
class TektronixAFG(RealDriver, FunctionGenerator):
    """Driver for Tektronix AFG3000 Series Arbitrary Function Generators."""

    def __init__(self, resource: str, channel: int = 1):
        super().__init__(resource)
        self.channel = channel
        self.ch_prefix = f"SOURce{channel}"

    def preset(self, automation_optimized: bool = True):
        self.write("*RST")
        self.wait_ready()

    def set_frequency(self, hz: float):
        self.write(f"{self.ch_prefix}:FREQuency:FIXed {hz}")

    def set_amplitude(self, dbm: float):
        """AFGs typically use Voltage. Converting dBm to Vpp (approx 50 Ohm)."""
        vpp = 2 * (10 ** ((dbm - 10) / 20))
        self.set_voltage(vpp)

    def set_voltage(self, vpp: float):
        self.write(f"{self.ch_prefix}:VOLTage:AMPLitude {vpp}")

    def set_offset(self, volts: float):
        self.write(f"{self.ch_prefix}:VOLTage:LEVel:IMMediate:OFFSet {volts}")

    def set_waveform(self, shape: str):
        # SINusoid, SQUare, PULSe, RAMP, PRNoise, DC
        full_names = {
            "SIN": "SINUSOID",
            "SQU": "SQUARE",
            "PULS": "PULSE",
            "RAMP": "RAMP",
            "PRN": "PRNOISE",
            "DC": "DC"
        }
        name = full_names.get(shape.upper(), shape.upper())
        self.write(f"{self.ch_prefix}:FUNCtion:SHAPe {name}")

    def set_output(self, state: bool):
        self.write(f"OUTPut{self.channel}:STATe {'ON' if state else 'OFF'}")

    def set_mod_state(self, mod_type: str, state: bool):
        # Basic AM/FM/PM/FSK/PWM
        self.write(f"{self.ch_prefix}:{mod_type.upper()}:STATe {'ON' if state else 'OFF'}")

    def start_sweep(self, start: float, stop: float, points: int, dwell: float):
        self.write(f"{self.ch_prefix}:SWEep:STARt {start}")
        self.write(f"{self.ch_prefix}:SWEep:STOP {stop}")
        self.write(f"{self.ch_prefix}:SWEep:TIME {dwell * points}")
        self.write(f"{self.ch_prefix}:SWEep:STATe ON")

    def configure_list_sweep(self, freq_list: List[float], power_list: List[float]):
        self._unsupported_feature("List Sweep (Use ARB mode instead)")

    def set_reference_clock(self, source: str):
        self.write(f"SOURce:ROSCillator:SOURce {source.upper()}")

    def shutdown_safety(self):
        self.set_output(False)
        self.sync_config()
