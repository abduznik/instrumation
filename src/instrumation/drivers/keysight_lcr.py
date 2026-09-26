from .base import LCRMeter
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("LCR")
class KeysightE4980A(RealDriver, LCRMeter):
    """Driver for Keysight E4980A/AL Precision LCR Meters.

    SCPI Reference (E4980A/AL User's Guide):
        - :FREQuency[:CW] <hz>
        - :VOLTage[:LEVel] <volts>
        - :CURRent[:LEVel] <amps>
        - :FUNCtion:IMPedance[:TYPE] {CPD|CPQ|CPG|CPRP|CSD|CSQ|CSRS|
          LPD|LPQ|LPG|LPRP|LPRD|LSD|LSQ|LSRS|LSRD|RX|ZTD|ZTR|GB|YTD|
          YTR|VDID}
        - :FUNCtion:IMPedance:RANGe:AUTO {ON|OFF}
        - :BIAS:VOLTage[:LEVel] <volts>
        - :BIAS:STATe {ON|OFF}
        - :FETCh[:IMPedance][:FORMatted]?  — returns "<primary>,<secondary>,<status>"
        - :TRIGger[:IMMediate]
    """

    def set_frequency(self, hz: float) -> None:
        self.safe_send(f"FREQ {hz}")

    def get_frequency(self) -> float:
        return float(self.query("FREQ?"))

    def set_voltage_level(self, volts: float) -> None:
        self.safe_send(f"VOLT {volts}")

    def set_current_level(self, amps: float) -> None:
        self.safe_send(f"CURR {amps}")

    def set_measurement_function(self, function: str) -> None:
        self.safe_send(f"FUNC:IMP {function.upper()}")

    def get_measurement_function(self) -> str:
        return self.query("FUNC:IMP?").strip()

    def set_auto_range(self, state: bool) -> None:
        self.safe_send(f"FUNC:IMP:RANG:AUTO {'ON' if state else 'OFF'}")

    def set_bias_voltage(self, volts: float) -> None:
        self.safe_send(f"BIAS:VOLT {volts}")

    def set_bias_state(self, state: bool) -> None:
        self.safe_send(f"BIAS:STAT {'ON' if state else 'OFF'}")

    def measure(self) -> MeasurementResult:
        resp = self.query_ascii("FETC:IMP:FORM?")
        parts = resp.split(",")
        primary = float(parts[0])
        secondary = float(parts[1]) if len(parts) > 1 else 0.0
        return MeasurementResult((primary, secondary), self.get_measurement_function())

    def trigger(self) -> None:
        """Sends an immediate trigger for a single measurement (:TRIGger[:IMMediate])."""
        self.write("TRIG:IMM")

    def shutdown_safety(self) -> None:
        self.set_bias_state(False)
        self.sync_config()
