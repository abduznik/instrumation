from .base import PowerSupply
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("PSU")
class SiglentSPD3303X(RealDriver, PowerSupply):
    """Driver for Siglent SPD3303X/SPD3303X-E Triple-Output DC Power Supplies.

    Validated Model: SPD3303X. CH1 and CH2 are independently controlled
    outputs; CH3 is a fixed 5V/2.5A logic supply with output on/off
    control only (no settable voltage/current). Commands address a
    channel directly via a ``CH1``/``CH2`` prefix or explicit
    ``MEAS:*? CH<n>`` argument -- no channel-select round-trip, unlike
    the BK Precision 9130B.

    SCPI Reference (SPD3303X Quick Start / Programming Guide):
        - {CH1|CH2}:VOLTage {<value>}
        - {CH1|CH2}:VOLTage?
        - {CH1|CH2}:CURRent {<value>}
        - {CH1|CH2}:CURRent?
        - OUTPut {CH1|CH2|CH3},{ON|OFF}
        - OUTPut? {CH1|CH2|CH3}
        - MEASure:VOLTage? {CH1|CH2}
        - MEASure:CURRent? {CH1|CH2}
        - MEASure:POWEr? {CH1|CH2}
        - OUTPut:TRACK {0|1|2}      — 0=independent, 1=series, 2=parallel
        - INSTrument {CH1|CH2}
        - *SAV {1-5} / *RCL {1-5}

    Unsupported: set_ovp/set_ocp (no software OVP/OCP commands), clear_protection.
    """

    def _ch(self, channel: int = None) -> str:
        return f"CH{channel}" if channel else "CH1"

    def preset(self, automation_optimized: bool = True) -> None:
        self.write("*RST")
        self.sync_config()

    def set_voltage(self, voltage: float, channel: int = None) -> None:
        self.safe_send(f"{self._ch(channel)}:VOLT {voltage}")

    def get_voltage(self, channel: int = None) -> float:
        return float(self.query_ascii(f"{self._ch(channel)}:VOLT?"))

    def set_current_limit(self, current: float, channel: int = None) -> None:
        self.safe_send(f"{self._ch(channel)}:CURR {current}")

    def get_current(self, channel: int = None) -> MeasurementResult:
        val = self.query_ascii(f"{self._ch(channel)}:CURR?")
        return MeasurementResult(float(val), "A")

    def set_output(self, state: bool, channel: int = None) -> None:
        self.write(f"OUTP {self._ch(channel)},{'ON' if state else 'OFF'}")

    def get_output(self, channel: int = None) -> bool:
        state = self.query_ascii(f"OUTP? {self._ch(channel)}")
        return state.strip().upper() == "ON"

    def measure_voltage_actual(self, channel: int = None) -> MeasurementResult:
        val = self.query_ascii(f"MEAS:VOLT? {self._ch(channel)}")
        return MeasurementResult(float(val), "V")

    def measure_current(self, channel: int = None) -> MeasurementResult:
        val = self.query_ascii(f"MEAS:CURR? {self._ch(channel)}")
        return MeasurementResult(float(val), "A")

    def measure_power(self, channel: int = None) -> MeasurementResult:
        val = self.query_ascii(f"MEAS:POWE? {self._ch(channel)}")
        return MeasurementResult(float(val), "W")

    def set_track_mode(self, mode: int) -> None:
        """Sets CH1/CH2 coupling: 0=independent, 1=series, 2=parallel."""
        if mode not in (0, 1, 2):
            raise ValueError("mode must be 0 (independent), 1 (series), or 2 (parallel)")
        self.write(f"OUTP:TRACK {mode}")

    def save_state(self, index: int) -> None:
        if not (1 <= index <= 5):
            raise ValueError("Index must be 1-5")
        self.write(f"*SAV {index}")

    def load_state(self, index: int) -> None:
        if not (1 <= index <= 5):
            raise ValueError("Index must be 1-5")
        self.write(f"*RCL {index}")

    def shutdown_safety(self) -> None:
        for ch in (1, 2, 3):
            self.set_output(False, channel=ch)
        self.sync_config()
