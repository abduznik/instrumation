"""Tests for the Siglent SDL1000X series DC electronic load driver.

The driver previously had no test coverage; the input-state query parsing is
the regression of interest here (Siglent SDL1000X Programming Guide p.18:
":SOURce:INPut[:STATe]? ... Return "1" if input status is ON. Otherwise,
return "0"").
"""
import pytest
from unittest.mock import MagicMock, patch

from instrumation.drivers.siglent import SiglentSDL1000X


@pytest.fixture
def mock_load():
    with patch('pyvisa.ResourceManager'):
        driver = SiglentSDL1000X("TCPIP::1.2.3.8::INSTR")
        driver.inst = MagicMock()
        driver.check_errors_enabled = False
        yield driver


def test_set_input(mock_load):
    mock_load.set_input(True)
    mock_load.inst.write.assert_any_call(":SOUR:INP:STAT ON")
    mock_load.set_input(False)
    mock_load.inst.write.assert_any_call(":SOUR:INP:STAT OFF")


def test_get_input_accepts_numeric_boolean(mock_load):
    """The SDL answers the input-state query with 1 (ON) or 0 (OFF)."""
    mock_load.inst.query.return_value = "1"
    assert mock_load.get_input() is True
    mock_load.inst.query.return_value = "1\n"
    assert mock_load.get_input() is True
    mock_load.inst.query.return_value = "0"
    assert mock_load.get_input() is False


def test_get_input_still_accepts_symbolic_boolean(mock_load):
    """Devices/fixtures that answer ON/OFF must keep working."""
    mock_load.inst.query.return_value = "ON"
    assert mock_load.get_input() is True


def test_set_get_mode(mock_load):
    mock_load.set_mode("cc")
    mock_load.inst.write.assert_any_call(":SOUR:FUNC CC")
    mock_load.inst.query.return_value = "CV"
    assert mock_load.get_mode() == "CV"


def test_set_mode_invalid_raises(mock_load):
    with pytest.raises(ValueError):
        mock_load.set_mode("XX")


def test_set_get_current(mock_load):
    mock_load.set_current(3.0)
    mock_load.inst.write.assert_any_call(":SOUR:CURR:LEV:IMM 3.0")
    mock_load.inst.query.return_value = "3.0"
    assert mock_load.get_current() == 3.0
