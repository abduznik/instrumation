from .base import InstrumentDriver
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("SENSOR")
class RohdeSchwarzNRPZ(RealDriver, InstrumentDriver):
    """Driver for Rohde & Schwarz NRP-Z Series USB Power Sensors.

    SCPI-99 power-sensor command set, similar in shape to the Keysight
    U2000 series but with R&S-specific correction/trigger subsystems
    (``SENSe:CORRection:DCYCle`` for pulse-power duty-cycle correction,
    ``SENSe:CORRection:SPDevice`` for S-parameter device correction).
    Like the U2000, this is a headless USB sensor with no front panel.

    SCPI Reference (NRP-Z Series Manual):
        - FETCh? / READ?              — power reading
        - INITiate:IMMediate / :CONTinuous {ON|OFF}
        - TRIGger:SOURce {HOLD|IMMediate|INTernal|BUS|EXTernal}
        - SENSe:FREQuency <hz>
        - SENSe:CORRection:OFFSet <db> / :OFFSet:STATe {ON|OFF}
        - SENSe:CORRection:DCYCle <percent> / :DCYCle:STATe {ON|OFF}
        - SENSe:CORRection:SPDevice:STATe {ON|OFF}
        - CALibration:ZERO:AUTO {ONCE|ON|OFF}
    """

    def set_frequency(self, hz: float) -> None:
        """Sets the CW frequency used for the sensor's cal-factor table lookup."""
        self.safe_send(f"SENS:FREQ {hz}")

    def get_frequency(self) -> float:
        return float(self.query("SENS:FREQ?"))

    def set_offset(self, db: float) -> None:
        """Sets a fixed gain/loss correction offset in dB."""
        self.safe_send(f"SENS:CORR:OFFS {db}")

    def set_offset_state(self, state: bool) -> None:
        self.safe_send(f"SENS:CORR:OFFS:STAT {'ON' if state else 'OFF'}")

    def set_duty_cycle(self, percent: float) -> None:
        """Sets the duty cycle percentage for pulse-power correction."""
        self.safe_send(f"SENS:CORR:DCYC {percent}")

    def set_duty_cycle_state(self, state: bool) -> None:
        self.safe_send(f"SENS:CORR:DCYC:STAT {'ON' if state else 'OFF'}")

    def set_sparameter_correction_state(self, state: bool) -> None:
        """Enables/disables S-parameter device correction."""
        self.safe_send(f"SENS:CORR:SPD:STAT {'ON' if state else 'OFF'}")

    def set_trigger_source(self, source: str) -> None:
        valid = {"HOLD", "IMMEDIATE", "INTERNAL", "BUS", "EXTERNAL"}
        if source.upper() not in valid:
            raise ValueError(f"Invalid trigger source: {source}")
        self.safe_send(f"TRIG:SOUR {source.upper()}")

    def zero(self) -> None:
        """Performs a one-time zero calibration (CAL:ZERO:AUTO ONCE)."""
        self.write("CAL:ZERO:AUTO ONCE")
        self.wait_ready()

    def measure_power(self) -> MeasurementResult:
        return self._meas("FETC?", "dBm")

    def shutdown_safety(self) -> None:
        self.sync_config()
