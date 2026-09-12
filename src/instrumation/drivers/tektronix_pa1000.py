import time
from .base import InstrumentDriver
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("POWERMETER")
class TektronixPA1000(RealDriver, InstrumentDriver):
    """Driver for Tektronix PA1000 Single-Phase AC Power Analyzer.

    Has several documented SCPI quirks (confirmed against real-world
    PyVISA usage notes, since Tektronix's published manual omits the
    programming chapter):
        - Every command requires the leading ``:`` root designator,
          even for commands that would normally allow it to be omitted.
        - Semicolon-separated command chaining is NOT supported --
          each command must be sent and (for setters) given time to
          take effect separately.
        - No ``*OPC?`` support -- this driver overrides ``wait_ready``
          to sleep a fixed delay instead of polling.
        - Setting commands need ~0.5s to take effect; ``*RST`` needs
          5-10s before the instrument responds again.
        - Responses are always CR-terminated (LF follows for query
          responses); PyVISA's default termination handles this via
          the resource manager's ``read_termination``.

    Command Reference (community-verified, PA1000 lacks a published
    SCPI programming chapter):
        - :SEL:CLR                       — clear all selected readings
        - :SEL:VLT / :SEL:CURrent / :SEL:PWR / :SEL:FRQ / :SEL:PWRFactor
          — select a reading for inclusion in :FRD? output
        - :RNG:VLT AUTo / :RNG:CURrent AUTo   — auto-range voltage/current
        - :SYSTem:ZERO 1                 — enable auto-zero
        - :FRF?                          — retrieve the configured reading list
        - :DSR?                          — read the data status register
        - :FRD?                          — fetch reading data (comma-separated)
    """

    _SETTER_DELAY_S = 0.5
    _RESET_DELAY_S = 5.0

    def wait_ready(self, timeout: float = 30.0) -> None:
        """PA1000 has no *OPC? support; sleep a fixed settle time instead."""
        time.sleep(self._SETTER_DELAY_S)

    def preset(self, automation_optimized: bool = True) -> None:
        self.write("*RST")
        time.sleep(self._RESET_DELAY_S)

    def clear_selection(self) -> None:
        self.write(":SEL:CLR")
        self.wait_ready()

    def select_voltage(self) -> None:
        self.write(":SEL:VLT")
        self.wait_ready()

    def select_current(self) -> None:
        self.write(":SEL:CURR")
        self.wait_ready()

    def select_power(self) -> None:
        self.write(":SEL:PWR")
        self.wait_ready()

    def select_frequency(self) -> None:
        self.write(":SEL:FRQ")
        self.wait_ready()

    def select_power_factor(self) -> None:
        self.write(":SEL:PWRF")
        self.wait_ready()

    def set_auto_range_voltage(self) -> None:
        self.write(":RNG:VLT AUT")
        self.wait_ready()

    def set_auto_range_current(self) -> None:
        self.write(":RNG:CURR AUT")
        self.wait_ready()

    def set_auto_zero(self, state: bool) -> None:
        self.write(f":SYST:ZERO {'1' if state else '0'}")
        self.wait_ready()

    def get_reading_list(self) -> str:
        """Queries the currently configured reading list (:FRF?)."""
        return self.query(":FRF?")

    def get_data_status(self) -> str:
        """Reads the data status register (:DSR?)."""
        return self.query(":DSR?")

    def fetch_readings(self) -> MeasurementResult:
        """Fetches the currently configured readings as a comma-separated list."""
        resp = self.query(":FRD?")
        values = [float(v) for v in resp.split(",") if v.strip()]
        return MeasurementResult(values, "mixed")

    def measure_voltage_rms(self) -> MeasurementResult:
        self.clear_selection()
        self.select_voltage()
        res = self.fetch_readings()
        val = res.value[0] if res.value else 0.0
        return MeasurementResult(val, "V")

    def measure_current_rms(self) -> MeasurementResult:
        self.clear_selection()
        self.select_current()
        res = self.fetch_readings()
        val = res.value[0] if res.value else 0.0
        return MeasurementResult(val, "A")

    def measure_active_power(self) -> MeasurementResult:
        self.clear_selection()
        self.select_power()
        res = self.fetch_readings()
        val = res.value[0] if res.value else 0.0
        return MeasurementResult(val, "W")

    def measure_frequency(self) -> MeasurementResult:
        self.clear_selection()
        self.select_frequency()
        res = self.fetch_readings()
        val = res.value[0] if res.value else 0.0
        return MeasurementResult(val, "Hz")

    def measure_duty_cycle(self) -> MeasurementResult:
        return MeasurementResult(0.0, "%")

    def measure_v_peak_to_peak(self) -> MeasurementResult:
        return MeasurementResult(0.0, "V")

    def shutdown_safety(self) -> None:
        self.sync_config()
