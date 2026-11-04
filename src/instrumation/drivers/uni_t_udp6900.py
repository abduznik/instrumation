from .base import PowerSupply
from .registry import register_driver
from .real import RealDriver, SaveRecallSlots
from ..results import MeasurementResult


@register_driver("PSU")
class UniTUDP6900(SaveRecallSlots, RealDriver, PowerSupply):
    """Driver for UNI-T UDP6900 Series single-output programmable DC power supplies.

    Validated Model: UDP6900. Single output, 0-150 V / 0-10 A, 600 W.
    SCPI is case-insensitive; commands use the [:SOURce:] subtree (the
    SOURce prefix is optional per the manual) and there is no channel
    addressing since there is one output. Every ``PowerSupply`` interface
    method accepts an optional ``channel=`` (ignored; defaults to the single
    output).

    SCPI Reference (UDP6900 Series SCPI Programming Manual V1.1):
        - [:SOURce]:VOLTage[:LEVel][:IMMediate][:AMPLitude] {<v>|MIN|MAX}
        - [:SOURce]:VOLTage[:LEVel][:IMMediate][:AMPLitude]?
        - [:SOURce]:CURRent[:LEVel][:IMMediate][:AMPLitude] {<i>|MIN|MAX}
        - [:SOURce]:CURRent[:LEVel][:IMMediate][:AMPLitude]?
        - [:SOURce]:VOLTage:PROTection[:LEVel] {<v>|MIN|MAX}
        - [:SOURce]:VOLTage:PROTection:STATe {ON|OFF}
        - [:SOURce]:CURRent:PROTection[:LEVel] {<i>|MIN|MAX}
        - [:SOURce]:CURRent:PROTection:STATe {ON|OFF}
        - [:SOURce]:VOLTage:PROTection:TRIPed?
        - [:SOURce]:VOLTage:PROTection:CLEar
        - [:SOURce]:CURRent:PROTection:TRIPed?
        - [:SOURce]:CURRent:PROTection:CLEar
        - :OUTPut[:STATe] {ON|OFF}
        - :OUTPut[:STATe]?
        - :OUTPut:CVCC?
        - :OUTPut:OVP:VALue <v>
        - :OUTPut:OCP:VALue <i>
        - :OUTPut:OVP[:STATe] {ON|OFF}
        - :OUTPut:OCP[:STATe] {ON|OFF}
        - :MEASure[:VOLTage]?
        - :MEASure:CURRent?
        - :MEASure:POWEr?
        - :MEASure:ALL?
        - *SAV {1-10} / *RCL {1-10}
    """

    STATE_SLOTS = range(1, 11)
    CHANNELS = (1,)

    def preset(self, automation_optimized: bool = True) -> None:
        self.write("*RST")
        self.wait_ready()

    def set_voltage(self, voltage: float, channel: int = None) -> None:
        self.safe_send(f":SOURce:VOLTage {voltage}")

    def get_voltage(self, channel: int = None) -> float:
        return float(self.query_ascii(":SOURce:VOLTage?"))

    def set_current_limit(self, current: float, channel: int = None) -> None:
        self.safe_send(f":SOURce:CURRent {current}")

    def get_current(self, channel: int = None) -> MeasurementResult:
        return self._meas(":SOURce:CURRent?", "A")

    def set_output(self, state: bool, channel: int = None) -> None:
        self.write(f":OUTPut {'ON' if state else 'OFF'}")

    def get_output(self, channel: int = None) -> bool:
        state = self.query_ascii(":OUTPut?")
        return state.strip().upper() == "ON"

    def set_ovp(self, voltage: float, channel: int = None) -> None:
        self.write(f":SOURce:VOLTage:PROTection {voltage}")
        self.write(":SOURce:VOLTage:PROTection:STATe ON")

    def get_ovp(self, channel: int = None) -> float:
        return float(self.query(":SOURce:VOLTage:PROTection?"))

    def set_ocp(self, current: float, channel: int = None) -> None:
        self.write(f":SOURce:CURRent:PROTection {current}")
        self.write(":SOURce:CURRent:PROTection:STATe ON")

    def get_ocp(self, channel: int = None) -> float:
        return float(self.query(":SOURce:CURRent:PROTection?"))

    def clear_protection(self, channel: int = None) -> None:
        self.write(":SOURce:VOLTage:PROTection:CLEar")
        self.write(":SOURce:CURRent:PROTection:CLEar")

    def measure_voltage_actual(self, channel: int = None) -> MeasurementResult:
        return self._meas(":MEASure:VOLTage?", "V")

    def measure_current(self, channel: int = None) -> MeasurementResult:
        return self._meas(":MEASure:CURRent?", "A")

    def measure_power(self, channel: int = None) -> MeasurementResult:
        return self._meas(":MEASure:POWEr?", "W")

    def shutdown_safety(self) -> None:
        self.set_output(False)
        self.set_voltage(0.0)
        self.set_current_limit(0.0)
        self.sync_config()
