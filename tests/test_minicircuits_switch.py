import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.minicircuits_switch import MiniCircuitsRCSwitch


@pytest.fixture
def mock_switch():
    with patch('pyvisa.ResourceManager'):
        driver = MiniCircuitsRCSwitch("TCPIP::1.2.3.30::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        yield driver


def test_get_id(mock_switch):
    mock_switch.inst.query.return_value = "RC-4SPDT-A18"
    assert mock_switch.get_id() == "RC-4SPDT-A18"
    mock_switch.inst.query.assert_any_call("MN?")


def test_set_switch(mock_switch):
    mock_switch.set_switch("a", True)
    mock_switch.inst.write.assert_any_call("SETA=1")
    mock_switch.set_switch("b", False)
    mock_switch.inst.write.assert_any_call("SETB=0")


def test_get_switch(mock_switch):
    mock_switch.inst.query.return_value = "1"
    assert mock_switch.get_switch("a") is True
    mock_switch.inst.query.return_value = "0"
    assert mock_switch.get_switch("a") is False


def test_set_port(mock_switch):
    mock_switch.set_port(1, 4, 3)
    mock_switch.inst.write.assert_any_call("SP4T:STATE:PORT 3")


def test_get_port(mock_switch):
    mock_switch.inst.query.return_value = "2"
    assert mock_switch.get_port(4) == 2
    mock_switch.inst.query.assert_any_call("SP4T:STATE:PORT?")


def test_get_all_switches_bitmask(mock_switch):
    mock_switch.inst.query.return_value = "5"
    assert mock_switch.get_all_switches_bitmask() == 5
    mock_switch.inst.query.assert_any_call("GETSWITCH?")


def test_get_serial_number(mock_switch):
    mock_switch.inst.query.return_value = "12345"
    assert mock_switch.get_serial_number() == "12345"


def test_get_firmware_version(mock_switch):
    mock_switch.inst.query.return_value = "A1"
    assert mock_switch.get_firmware_version() == "A1"


def test_check_errors_is_noop(mock_switch):
    mock_switch.check_errors()
    mock_switch.inst.query.assert_not_called()


def test_unsupported_measures_return_zero(mock_switch):
    assert mock_switch.measure_frequency().value == 0.0
    assert mock_switch.measure_duty_cycle().value == 0.0
    assert mock_switch.measure_v_peak_to_peak().value == 0.0
