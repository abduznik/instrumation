import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.prodigit_load import Prodigit3311F


@pytest.fixture
def mock_load():
    with patch('pyvisa.ResourceManager'):
        driver = Prodigit3311F("GPIB0::12::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "0"
        driver.check_errors_enabled = False
        yield driver


def test_set_mode_selects_slot(mock_load):
    mock_load.set_mode("CC", slot=2)
    mock_load.inst.write.assert_any_call("CHAN2")
    mock_load.inst.write.assert_any_call("MODE:CC")


def test_set_mode_invalid_raises(mock_load):
    with pytest.raises(ValueError):
        mock_load.set_mode("BOGUS")


def test_get_mode(mock_load):
    mock_load.inst.query.return_value = "CV"
    assert mock_load.get_mode(slot=1) == "CV"
    mock_load.inst.write.assert_any_call("CHAN1")


def test_set_current(mock_load):
    mock_load.set_current(5.0, slot=1)
    mock_load.inst.write.assert_any_call("CURR 5.0")


def test_get_current(mock_load):
    mock_load.inst.query.return_value = "2.5"
    assert mock_load.get_current() == 2.5


def test_set_voltage(mock_load):
    mock_load.set_voltage(12.0)
    mock_load.inst.write.assert_any_call("VOLT 12.0")


def test_get_voltage(mock_load):
    mock_load.inst.query.return_value = "12.0"
    assert mock_load.get_voltage() == 12.0


def test_set_resistance(mock_load):
    mock_load.set_resistance(10.0)
    mock_load.inst.write.assert_any_call("RES 10.0")


def test_get_resistance(mock_load):
    mock_load.inst.query.return_value = "10.0"
    assert mock_load.get_resistance() == 10.0


def test_set_power(mock_load):
    mock_load.set_power(50.0)
    mock_load.inst.write.assert_any_call("POW 50.0")


def test_get_power(mock_load):
    mock_load.inst.query.return_value = "50.0"
    assert mock_load.get_power() == 50.0


def test_set_input_on_off(mock_load):
    mock_load.set_input(True)
    mock_load.inst.write.assert_any_call("LOAD ON")
    mock_load.set_input(False)
    mock_load.inst.write.assert_any_call("LOAD OFF")


def test_get_input(mock_load):
    mock_load.inst.query.return_value = "1"
    assert mock_load.get_input() is True
    mock_load.inst.query.return_value = "0"
    assert mock_load.get_input() is False


def test_measure_voltage(mock_load):
    mock_load.inst.query.return_value = "11.998"
    res = mock_load.measure_voltage()
    assert res.value == 11.998
    assert res.unit == "V"
    mock_load.inst.query.assert_any_call("MEAS:VOLT?")


def test_measure_current(mock_load):
    mock_load.inst.query.return_value = "4.998"
    res = mock_load.measure_current()
    assert res.value == 4.998
    mock_load.inst.query.assert_any_call("MEAS:CURR?")


def test_measure_power(mock_load):
    mock_load.inst.query.return_value = "59.9"
    res = mock_load.measure_power()
    assert res.value == 59.9
    assert res.unit == "W"
    mock_load.inst.query.assert_any_call("MEAS:POW?")


def test_set_ovp(mock_load):
    mock_load.set_ovp(65.0)
    mock_load.inst.write.assert_any_call("VOLT:PROT 65.0")


def test_set_ocp(mock_load):
    mock_load.set_ocp(65.0)
    mock_load.inst.write.assert_any_call("CURR:PROT 65.0")


def test_set_opp(mock_load):
    mock_load.set_opp(310.0)
    mock_load.inst.write.assert_any_call("POW:PROT 310.0")


def test_clear_protection(mock_load):
    mock_load.clear_protection()
    mock_load.inst.write.assert_any_call("PROT:CLE")


def test_shutdown_safety(mock_load):
    mock_load.shutdown_safety()
    mock_load.inst.write.assert_any_call("LOAD OFF")
