import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.sorensen_psu import SorensenSG


@pytest.fixture
def mock_psu():
    with patch('pyvisa.ResourceManager'):
        driver = SorensenSG("GPIB0::10::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "0"
        driver.check_errors_enabled = False
        yield driver


def test_set_voltage(mock_psu):
    mock_psu.set_voltage(24.0)
    mock_psu.inst.write.assert_any_call("SOUR:VOLT 24.0")


def test_get_voltage(mock_psu):
    mock_psu.inst.query.return_value = "24.0"
    assert mock_psu.get_voltage() == 24.0
    mock_psu.inst.query.assert_any_call("SOUR:VOLT?")


def test_set_current_limit(mock_psu):
    mock_psu.set_current_limit(5.0)
    mock_psu.inst.write.assert_any_call("SOUR:CURR 5.0")


def test_get_current(mock_psu):
    mock_psu.inst.query.return_value = "2.5"
    res = mock_psu.get_current()
    assert res.value == 2.5
    assert res.unit == "A"


def test_set_output_on_off(mock_psu):
    mock_psu.set_output(True)
    mock_psu.inst.write.assert_any_call("OUTP:STAT ON")
    mock_psu.set_output(False)
    mock_psu.inst.write.assert_any_call("OUTP:STAT OFF")


def test_get_output(mock_psu):
    mock_psu.inst.query.return_value = "1"
    assert mock_psu.get_output() is True
    mock_psu.inst.query.return_value = "0"
    assert mock_psu.get_output() is False


def test_set_ovp(mock_psu):
    mock_psu.set_ovp(30.0)
    mock_psu.inst.write.assert_any_call("SOUR:VOLT:PROT 30.0")


def test_set_ocp(mock_psu):
    mock_psu.set_ocp(6.0)
    mock_psu.inst.write.assert_any_call("SOUR:CURR:PROT 6.0")


def test_clear_protection(mock_psu):
    mock_psu.clear_protection()
    mock_psu.inst.write.assert_any_call("OUTP:PROT:CLE")


def test_measure_voltage_actual(mock_psu):
    mock_psu.inst.query.return_value = "23.998"
    res = mock_psu.measure_voltage_actual()
    assert res.value == 23.998
    assert res.unit == "V"
    mock_psu.inst.query.assert_any_call("MEAS:VOLT?")


def test_measure_current(mock_psu):
    mock_psu.inst.query.return_value = "1.501"
    res = mock_psu.measure_current()
    assert res.value == 1.501
    mock_psu.inst.query.assert_any_call("MEAS:CURR?")


def test_shutdown_safety(mock_psu):
    mock_psu.shutdown_safety()
    mock_psu.inst.write.assert_any_call("OUTP:STAT OFF")
    mock_psu.inst.write.assert_any_call("SOUR:VOLT 0.0")
