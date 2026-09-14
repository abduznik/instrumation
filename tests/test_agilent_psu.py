import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.agilent_psu import Agilent6632B


@pytest.fixture
def mock_psu():
    with patch('pyvisa.ResourceManager'):
        driver = Agilent6632B("GPIB0::5::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "0"
        driver.check_errors_enabled = False
        yield driver


def test_set_voltage(mock_psu):
    mock_psu.set_voltage(12.0)
    mock_psu.inst.write.assert_any_call("VOLT 12.0")


def test_get_voltage(mock_psu):
    mock_psu.inst.query.return_value = "5.0"
    assert mock_psu.get_voltage() == 5.0
    mock_psu.inst.query.assert_any_call("VOLT?")


def test_set_current_limit(mock_psu):
    mock_psu.set_current_limit(2.5)
    mock_psu.inst.write.assert_any_call("CURR 2.5")


def test_get_current(mock_psu):
    mock_psu.inst.query.return_value = "1.2"
    res = mock_psu.get_current()
    assert res.value == 1.2
    assert res.unit == "A"


def test_set_output_on_off(mock_psu):
    mock_psu.set_output(True)
    mock_psu.inst.write.assert_any_call("OUTP ON")
    mock_psu.set_output(False)
    mock_psu.inst.write.assert_any_call("OUTP OFF")


def test_get_output(mock_psu):
    mock_psu.inst.query.return_value = "1"
    assert mock_psu.get_output() is True
    mock_psu.inst.query.return_value = "0"
    assert mock_psu.get_output() is False


def test_set_ovp(mock_psu):
    mock_psu.set_ovp(30.0)
    mock_psu.inst.write.assert_any_call("VOLT:PROT 30.0")


def test_set_ocp_sets_current_and_enables(mock_psu):
    mock_psu.set_ocp(3.0)
    mock_psu.inst.write.assert_any_call("CURR 3.0")
    mock_psu.inst.write.assert_any_call("CURR:PROT:STAT ON")


def test_clear_protection(mock_psu):
    mock_psu.clear_protection()
    mock_psu.inst.write.assert_any_call("OUTP:PROT:CLE")


def test_measure_voltage_actual(mock_psu):
    mock_psu.inst.query.return_value = "4.998"
    res = mock_psu.measure_voltage_actual()
    assert res.value == 4.998
    assert res.unit == "V"
    mock_psu.inst.query.assert_any_call("MEAS:VOLT?")


def test_measure_current(mock_psu):
    mock_psu.inst.query.return_value = "0.501"
    res = mock_psu.measure_current()
    assert res.value == 0.501
    mock_psu.inst.query.assert_any_call("MEAS:CURR?")


def test_set_autostart(mock_psu):
    mock_psu.set_autostart(True)
    mock_psu.inst.write.assert_any_call("OUTP:PON:STAT RCL0")
    mock_psu.set_autostart(False)
    mock_psu.inst.write.assert_any_call("OUTP:PON:STAT RST")


def test_shutdown_safety(mock_psu):
    mock_psu.shutdown_safety()
    mock_psu.inst.write.assert_any_call("OUTP OFF")
    mock_psu.inst.write.assert_any_call("VOLT 0.0")
