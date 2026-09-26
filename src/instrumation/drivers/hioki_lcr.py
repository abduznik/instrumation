from .base import LCRMeter
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("LCR")
class HiokiIM3536(RealDriver, LCRMeter):
    """Driver for Hioki IM3536 LCR Meter.

    SCPI-style command set shared across the IM3523/IM3533/IM3536/
    IM3570/IM3590 family (per Hioki's Communication Instruction
    Manual). Confirmed against Hioki's own PLC-integration examples
    for the `:FREQ`/`:FREQ?` command pair; parameter-type selection
    and measurement readback follow the same `:FUNC:IMP`/`:MEASure?`
    shape documented for the Keysight E4980A LCR meter class.

    SCPI Reference (IM3536 Communication Instruction Manual):
        - :FREQuency <hz> / :FREQuency?
        - :VOLTage:LEVel <volts> / :VOLTage:LEVel?
        - :FUNCtion:IMPedance <type>   — e.g. CPD, CSD, LSD, RX, ZTD
        - :FUNCtion:IMPedance:RANGe:AUTO {ON|OFF}
        - :BIAS:VOLTage:LEVel <volts>
        - :BIAS:STATe {ON|OFF}
        - :MEASure?                    — returns "<primary>,<secondary>"
        - :TRIGger

    > [!NOTE]
    > This driver is best-effort: the full IM3536 command reference
    > requires a Hioki-issued LCR Application Disc not published as a
    > standalone PDF. Verify against real hardware and prefer the
    > `"GENERIC"` fallback if a command errors.
    """

    def set_frequency(self, hz: float) -> None:
        self.safe_send(f":FREQ {hz}")

    def get_frequency(self) -> float:
        return float(self.query(":FREQ?"))

    def set_voltage_level(self, volts: float) -> None:
        self.safe_send(f":VOLT:LEV {volts}")

    def set_measurement_function(self, function: str) -> None:
        self.safe_send(f":FUNC:IMP {function.upper()}")

    def get_measurement_function(self) -> str:
        return self.query(":FUNC:IMP?").strip()

    def set_auto_range(self, state: bool) -> None:
        self.safe_send(f":FUNC:IMP:RANG:AUTO {'ON' if state else 'OFF'}")

    def set_bias_voltage(self, volts: float) -> None:
        self.safe_send(f":BIAS:VOLT:LEV {volts}")

    def set_bias_state(self, state: bool) -> None:
        self.safe_send(f":BIAS:STAT {'ON' if state else 'OFF'}")

    def measure(self) -> MeasurementResult:
        resp = self.query_ascii(":MEAS?")
        parts = resp.split(",")
        primary = float(parts[0])
        secondary = float(parts[1]) if len(parts) > 1 else 0.0
        return MeasurementResult((primary, secondary), self.get_measurement_function())

    def trigger(self) -> None:
        """Sends a single measurement trigger (:TRIGger)."""
        self.write(":TRIG")

    def shutdown_safety(self) -> None:
        self.set_bias_state(False)
        self.sync_config()
