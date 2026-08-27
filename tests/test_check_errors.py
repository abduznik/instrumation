"""Issue #157: check_errors must not rely on a "Mock" class-name hack.

Produces the real error-checking behavior with a plain fake that is NOT a
MagicMock (so the old `if "Mock" in type(self.inst).__name__` check would
have wrongly skipped it, and it was a test-detection hack in production
code masking real bugs).
"""
import unittest
from unittest.mock import MagicMock

from instrumation.drivers.real import RealDriver
from instrumation.exceptions import ConfigurationError


class _PlainFake:
    """Non-Magic fake whose class name does NOT contain 'Mock'."""

    def __init__(self, error_response=None):
        self._error_response = error_response
        self.calls = []

    def query(self, cmd):
        self.calls.append(cmd)
        return self._error_response if self._error_response is not None else '+0,"No error"'


class TestCheckErrorsNoMockHack(unittest.TestCase):
    def setUp(self):
        self.drv = RealDriver("GPIB0::1::INSTR")

    def test_plain_fake_clear_error_no_raise(self):
        """A non-Mock fake returning 'No error' must not raise."""
        self.drv.inst = _PlainFake('+0,"No error"')
        self.drv.check_errors()  # no exception

    def test_plain_fake_raises_on_hardware_error(self):
        """A non-Mock fake returning an error must raise ConfigurationError."""
        self.drv.inst = _PlainFake('-221,"Settings conflict"')
        with self.assertRaises(ConfigurationError):
            self.drv.check_errors()
        self.assertIn('-221,"Settings conflict"', self.drv.error_stack)

    def test_magicmock_still_works(self):
        """MagicMock-backed tests must keep working after removing the hack."""
        m = MagicMock()
        m.query.return_value = '+0,"No error"'
        self.drv.inst = m
        self.drv.check_errors()  # no exception

    def test_real_error_string_variant(self):
        """Error format '22,"Param error"' must also raise."""
        self.drv.inst = _PlainFake('22,"Param error"')
        with self.assertRaises(ConfigurationError):
            self.drv.check_errors()


if __name__ == "__main__":
    unittest.main()