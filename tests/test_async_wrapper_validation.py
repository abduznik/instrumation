"""Issue #166: async_ wrapper must validate the wrapped attribute.

Previously __getattr__ silently created async_<anything> wrappers for any
sync name that existed, including typos and non-callable attributes.
"""
import unittest

from instrumation.drivers.base import InstrumentDriver
from instrumation.results import MeasurementResult


class _Probe(InstrumentDriver):
    """Minimal driver with one callable method and one attribute."""

    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    def write(self, command: str) -> None: ...
    def query(self, command: str) -> str:
        return "ok"

    def safe_send(self, command: str) -> None:
        self.write(command)

    def query_ascii(self, command: str) -> str:
        return self.query(command)

    def query_binary_values(self, command: str, datatype: str = "f", is_big_endian: bool = False):
        return []

    def get_id(self) -> str:
        return "PROBE"

    def preset(self, automation_optimized: bool = True) -> None: ...
    def clear_status(self) -> None: ...
    def sync_config(self) -> None: ...
    def wait_ready(self, timeout: float = 30.0) -> None: ...
    def shutdown_safety(self) -> None: ...
    def check_errors(self) -> None: ...

    def measure_frequency(self) -> MeasurementResult:
        return MeasurementResult(0.0, "Hz")

    def measure_duty_cycle(self) -> MeasurementResult:
        return MeasurementResult(0.0, "%")

    def measure_v_peak_to_peak(self) -> MeasurementResult:
        return MeasurementResult(0.0, "V")

    # A non-callable attribute for the validation test
    max_power_dbm = 0.0


class TestAsyncWrapperValidation(unittest.TestCase):
    def setUp(self):
        self.drv = _Probe("USB::PROBE::INSTR")

    def test_async_wrapper_for_real_method(self):
        """async_<method> returns a coroutine wrapper for a callable method."""
        wrapper = self.drv.async_measure_frequency
        import asyncio
        res = asyncio.run(wrapper())
        self.assertIsInstance(res, MeasurementResult)

    def test_typo_async_name_raises_clear_error(self):
        """async_mesure_frequency (sic) must fail with a helpful AttributeError."""
        with self.assertRaises(AttributeError) as cm:
            self.drv.async_mesure_frequency
        self.assertIn("mesure_frequency", str(cm.exception))
        self.assertIn("async_", str(cm.exception))

    def test_non_callable_async_name_raises(self):
        """async_max_power_dbm wraps a float, not a method -> clear error."""
        with self.assertRaises(AttributeError) as cm:
            self.drv.async_max_power_dbm
        self.assertIn("non-callable", str(cm.exception))

    def test_plain_missing_attribute_still_raises(self):
        """Unrelated missing attributes keep the standard error."""
        with self.assertRaises(AttributeError):
            self.drv.nonexistent_thing


if __name__ == "__main__":
    unittest.main()