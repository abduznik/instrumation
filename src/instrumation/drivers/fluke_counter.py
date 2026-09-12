from .base import FrequencyCounter
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("COUNTER")
class FlukePM6690(RealDriver, FrequencyCounter):
    """Driver for Fluke PM6690 Timer/Counter/Analyzer.

    The PM6690 has two GPIB personalities: a native SCPI mode (targeted
    here) with a command set optimized for its own capabilities, and a
    compatible mode that emulates a Keysight/HP 53131A/53132A. Native
    mode uses the same standard SCPI-99 counter subsystem shape as
    ``Keysight53230A`` (``:MEASure:FREQuency?``, etc.).

    SCPI Reference (PM6690 Programming Manual):
        - :MEASure:FREQuency? [{range}]
        - :MEASure:PERiod? [{range}]
        - :MEASure:TINTerval? [{start_trigger},{stop_trigger}]
        - :INPut[1|2]:IMPedance {50|1E6}
        - :INPut[1|2]:LEVel {volts}
        - :INPut[1|2]:COUPling {DC|AC}
        - :INPut[1|2]:RANGe:AUTO {ON|OFF}
    """

    def __init__(self, resource: str) -> None:
        super().__init__(resource)
        self.min_frequency = 0.0
        self.max_frequency = 300e6
        self._active_channel = 1

    def _ch(self, channel: int = None) -> str:
        ch = channel if channel else self._active_channel
        return f"INP{ch}"

    def preset(self, automation_optimized: bool = True) -> None:
        self.write("*RST")
        self.wait_ready()

    def measure_frequency(self, range: str = "AUTO") -> MeasurementResult:
        if range.upper() == "AUTO":
            val = self.query_ascii(":MEAS:FREQ?")
        else:
            val = self.query_ascii(f":MEAS:FREQ? {range}")
        return MeasurementResult(float(val), "Hz")

    def measure_period(self, range: str = "AUTO") -> MeasurementResult:
        if range.upper() == "AUTO":
            val = self.query_ascii(":MEAS:PER?")
        else:
            val = self.query_ascii(f":MEAS:PER? {range}")
        return MeasurementResult(float(val), "s")

    def measure_time_interval(self, start_trigger: str, stop_trigger: str) -> MeasurementResult:
        val = self.query_ascii(f":MEAS:TINT? {start_trigger},{stop_trigger}")
        return MeasurementResult(float(val), "s")

    def set_impedance(self, ohms: float, channel: int = None) -> None:
        self.safe_send(f"{self._ch(channel)}:IMP {ohms}")

    def set_trigger_level(self, volts: float, channel: int = None) -> None:
        self.safe_send(f"{self._ch(channel)}:LEV {volts}")

    def set_coupling(self, dc_ac: str, channel: int = None) -> None:
        self.safe_send(f"{self._ch(channel)}:COUP {dc_ac.upper()}")

    def set_auto_range(self, state: bool, channel: int = None) -> None:
        self.safe_send(f"{self._ch(channel)}:RANG:AUTO {'ON' if state else 'OFF'}")

    def shutdown_safety(self) -> None:
        self.sync_config()
