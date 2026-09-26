from .base import LCRMeter
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("LCR")
class KeysightE4990A(RealDriver, LCRMeter):
    """Driver for the Keysight E4990A Impedance Analyzer (1 MHz - 120 MHz).

    Unlike the fixed-frequency `KeysightE4980A`/`HiokiIM3536` LCR
    meters, the E4990A sweeps frequency and returns trace data, closer
    in shape to `KeysightPNA` (VNA) but measuring impedance/LCR
    parameters instead of S-parameters. `LCRMeter.measure()` here
    performs a single-point measurement at the current CW frequency;
    `get_trace_data()` fetches a full swept trace.

    Command Reference (E4990A SCPI Command Reference):
        - SENSe:FREQuency:STARt <hz> / :STOP <hz> / :CW <hz>
        - SENSe:SWEep:POINts <n>
        - SENSe:SWEep:TYPE {LIN|LOG|SEGM}
        - CALCulate:PARameter1:DEFine {ZTD|ZTR|LSD|LSQ|CSD|CSQ|RX|...}
        - CALCulate:PARameter1:DEFine?
        - SOURce:VOLTage <v>  / SOURce:CURRent <a>
        - BIAS:VOLTage[:LEVel] <v> / BIAS:STATe {ON|OFF}
        - TRIGger:SOURce {INTernal|BUS|EXTernal}
        - TRIGger[:IMMediate] / *TRG
        - CALCulate:DATA:FDATa?               — formatted (primary,secondary) trace
        - CALCulate:DATA:SDATa?                — raw complex trace
        - DISPlay:WINDow:TRACe:Y:SCALe:AUTO
        - *IDN? / *RST / *CLS / *OPC?

    Fixture compensation (open/short/load cal) and equivalent-circuit
    fitting are explicitly out of scope for this driver, per issue #193.
    """

    def connect(self) -> None:
        super().connect()
        self.min_frequency = 1e6
        self.max_frequency = 120e6

    def set_frequency(self, hz: float) -> None:
        """Sets the CW test frequency (SENS:FREQ:CW) for single-point measurement."""
        self.safe_send(f"SENS:FREQ:CW {hz}")

    def get_frequency(self) -> float:
        return float(self.query_ascii("SENS:FREQ:CW?"))

    def set_start_frequency(self, hz: float) -> None:
        self.safe_send(f"SENS:FREQ:STAR {hz}")

    def get_start_frequency(self) -> float:
        return float(self.query_ascii("SENS:FREQ:STAR?"))

    def set_stop_frequency(self, hz: float) -> None:
        self.safe_send(f"SENS:FREQ:STOP {hz}")

    def get_stop_frequency(self) -> float:
        return float(self.query_ascii("SENS:FREQ:STOP?"))

    def set_points(self, num_points: int) -> None:
        self.safe_send(f"SENS:SWE:POIN {num_points}")

    def get_points(self) -> int:
        return int(float(self.query_ascii("SENS:SWE:POIN?")))

    def set_sweep_type(self, sweep_type: str) -> None:
        key = sweep_type.upper()
        if key not in ("LIN", "LOG", "SEGM"):
            raise ValueError(f"Invalid sweep type: {sweep_type}")
        self.safe_send(f"SENS:SWE:TYPE {key}")

    def set_voltage_level(self, volts: float) -> None:
        self.safe_send(f"SOUR:VOLT {volts}")

    def set_current_level(self, amps: float) -> None:
        self.safe_send(f"SOUR:CURR {amps}")

    def set_measurement_function(self, function: str) -> None:
        self.safe_send(f"CALC:PAR1:DEF {function.upper()}")

    def get_measurement_function(self) -> str:
        return self.query_ascii("CALC:PAR1:DEF?").strip()

    def set_bias_voltage(self, volts: float) -> None:
        self.safe_send(f"BIAS:VOLT {volts}")

    def set_bias_state(self, state: bool) -> None:
        self.safe_send(f"BIAS:STAT {'ON' if state else 'OFF'}")

    def set_trigger_source(self, source: str) -> None:
        key = source.upper()
        mapping = {"INTERNAL": "INT", "BUS": "BUS", "EXTERNAL": "EXT"}
        if key not in mapping and key not in mapping.values():
            raise ValueError(f"Invalid trigger source: {source}")
        self.safe_send(f"TRIG:SOUR {mapping.get(key, key)}")

    def trigger(self) -> None:
        """Sends an immediate trigger for a single sweep (TRIGger[:IMMediate])."""
        self.write("TRIG:IMM")

    def measure(self) -> MeasurementResult:
        """Single-point measurement at the current CW frequency (CALC:DATA:FDAT?)."""
        resp = self.query_ascii("CALC:DATA:FDAT?")
        parts = resp.split(",")
        primary = float(parts[0])
        secondary = float(parts[1]) if len(parts) > 1 else 0.0
        return MeasurementResult((primary, secondary), self.get_measurement_function())

    def get_trace_data(self) -> MeasurementResult:
        """Fetches the formatted (primary, secondary) trace across the full sweep."""
        resp = self.query_ascii("CALC:DATA:FDAT?")
        values = [float(v) for v in resp.split(",") if v.strip()]
        pairs = list(zip(values[0::2], values[1::2]))
        return MeasurementResult(pairs, self.get_measurement_function())

    def get_complex_trace(self) -> MeasurementResult:
        """Fetches the raw complex (real, imaginary) trace data (CALC:DATA:SDAT?)."""
        resp = self.query_ascii("CALC:DATA:SDAT?")
        values = [float(v) for v in resp.split(",") if v.strip()]
        complex_pairs = [complex(values[i], values[i + 1]) for i in range(0, len(values) - 1, 2)]
        return MeasurementResult(complex_pairs, "complex")

    def shutdown_safety(self) -> None:
        self.set_bias_state(False)
        self.sync_config()
