from .base import InstrumentDriver
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("SENSOR")
class KeysightU2000(RealDriver, InstrumentDriver):
    """Driver for Keysight U2000 Series USB Average Power Sensors.

    Standard SCPI power-sensor command set. Unlike bench instruments,
    the U2000 series is a USBTMC-only "headless" sensor -- there is no
    front panel, so all configuration happens over SCPI.

    SCPI Reference (U2000 Series USB Power Sensor Programming Guide):
        - FETCh[1][:SCALar][:POWer:AC]? [<expected>[,<resolution>[,<source>]]]
        - MEASure[1][:SCALar][:POWer:AC]? [<expected>[,<resolution>[,<source>]]]
        - READ[1][:SCALar][:POWer:AC]?
        - [SENSe[1]:]FREQuency[:CW|:FIXed] <hz>
        - [SENSe[1]:]CORRection:GAIN2:STATe {ON|OFF}
        - [SENSe[1]:]CORRection:GAIN2[:INPut][:MAGNitude] <db>
        - UNIT[1]:POWer {DBM|W}
        - CALibration[1]:ZERO:AUTO {ONCE|ON|OFF}
        - CALibration[1]:ZERO:TYPE {EXTernal|INTernal}
    """

    def preset(self, automation_optimized: bool = True) -> None:
        self.write("*RST")
        self.wait_ready()

    def set_frequency(self, hz: float) -> None:
        """Sets the CW frequency used for the sensor's cal-factor table lookup."""
        self.safe_send(f"SENS:FREQ {hz}")

    def get_frequency(self) -> float:
        return float(self.query("SENS:FREQ?"))

    def set_power_unit(self, unit: str) -> None:
        """Sets the readout unit: 'DBM' or 'W'."""
        unit_upper = unit.upper()
        if unit_upper not in ("DBM", "W"):
            raise ValueError("unit must be 'DBM' or 'W'")
        self.safe_send(f"UNIT:POW {unit_upper}")

    def set_gain_offset_state(self, state: bool) -> None:
        """Enables/disables the external gain/loss offset correction."""
        self.safe_send(f"SENS:CORR:GAIN2:STAT {'ON' if state else 'OFF'}")

    def set_gain_offset(self, db: float) -> None:
        """Sets the external gain/loss offset in dB (positive=gain, negative=loss)."""
        self.safe_send(f"SENS:CORR:GAIN2 {db}")

    def zero(self) -> None:
        """Performs a one-time internal zero calibration (CAL:ZERO:AUTO ONCE)."""
        self.write("CAL:ZERO:TYPE INT")
        self.write("CAL:ZERO:AUTO ONCE")
        self.wait_ready()

    def measure_power(self) -> MeasurementResult:
        val = self.query_ascii("FETC?")
        return MeasurementResult(float(val), "dBm")

    def shutdown_safety(self) -> None:
        self.sync_config()
