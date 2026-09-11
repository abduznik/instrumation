import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.rigol_load import RigolDL3021


@pytest.fixture
def mock_load():
    with patch('pyvisa.ResourceManager'):
        driver = RigolDL3021("TCPIP::1.2.3.16::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        driver.check_errors_enabled = False
        yield driver


def test_set_mode_valid(mock_load):
    mock_load.set_mode("cc")
    mock_load.inst.write.assert_any_call(":SOUR:FUNC CURR")
    mock_load.set_mode("CV")
    mock_load.inst.write.assert_any_call(":SOUR:FUNC VOLT")
    mock_load.set_mode("CR")
    mock_load.inst.write.assert_any_call(":SOUR:FUNC RES")
    mock_load.set_mode("CP")
    mock_load.inst.write.assert_any_call(":SOUR:FUNC POW")


def test_set_mode_invalid_raises(mock_load):
    with pytest.raises(ValueError):
        mock_load.set_mode("BOGUS")


def test_get_mode(mock_load):
    mock_load.inst.query.return_value = "CURR"
    assert mock_load.get_mode() == "CC"


def test_set_get_current(mock_load):
    mock_load.set_current(1.5)
    mock_load.inst.write.assert_any_call(":SOUR:CURR:LEV:IMM 1.5")
    mock_load.inst.query.return_value = "1.5"
    assert mock_load.get_current() == 1.5


def test_set_get_voltage(mock_load):
    mock_load.set_voltage(5.0)
    mock_load.inst.write.assert_any_call(":SOUR:VOLT:LEV:IMM 5.0")
    mock_load.inst.query.return_value = "5.0"
    assert mock_load.get_voltage() == 5.0


def test_set_get_resistance(mock_load):
    mock_load.set_resistance(100.0)
    mock_load.inst.write.assert_any_call(":SOUR:RES:LEV:IMM 100.0")
    mock_load.inst.query.return_value = "100.0"
    assert mock_load.get_resistance() == 100.0


def test_set_get_power(mock_load):
    mock_load.set_power(10.0)
    mock_load.inst.write.assert_any_call(":SOUR:POW:LEV:IMM 10.0")
    mock_load.inst.query.return_value = "10.0"
    assert mock_load.get_power() == 10.0


def test_set_input_on_off(mock_load):
    mock_load.set_input(True)
    mock_load.inst.write.assert_any_call(":SOUR:INP:STAT ON")
    mock_load.set_input(False)
    mock_load.inst.write.assert_any_call(":SOUR:INP:STAT OFF")


def test_get_input(mock_load):
    mock_load.inst.query.return_value = "1"
    assert mock_load.get_input() is True
    mock_load.inst.query.return_value = "0"
    assert mock_load.get_input() is False


def test_measure_voltage_current_power_resistance(mock_load):
    mock_load.inst.query.return_value = "4.999"
    res = mock_load.measure_voltage()
    assert res.value == 4.999
    assert res.unit == "V"

    mock_load.inst.query.return_value = "1.234"
    res = mock_load.measure_current()
    assert res.value == 1.234
    assert res.unit == "A"

    mock_load.inst.query.return_value = "5.5"
    res = mock_load.measure_power()
    assert res.value == 5.5
    assert res.unit == "W"

    mock_load.inst.query.return_value = "220.0"
    res = mock_load.measure_resistance()
    assert res.value == 220.0
    assert res.unit == "Ohm"


def test_protection_methods_are_unsupported_noop(mock_load):
    mock_load.set_ovp(30.0)
    mock_load.set_ocp(2.0)
    mock_load.set_opp(10.0)
    mock_load.clear_protection()


def test_set_battery_test_mode(mock_load):
    mock_load.set_battery_test_mode(True)
    mock_load.inst.write.assert_any_call(":SOUR:FUNC:MODE BATT")
    mock_load.set_battery_test_mode(False)
    mock_load.inst.write.assert_any_call(":SOUR:FUNC:MODE FIX")


def test_get_battery_test_capacity(mock_load):
    mock_load.inst.query.return_value = "2.5"
    res = mock_load.get_battery_test_capacity()
    assert res.value == 2.5
    assert res.unit == "Ah"


def test_get_watt_hours(mock_load):
    mock_load.inst.query.return_value = "12.3"
    res = mock_load.get_watt_hours()
    assert res.value == 12.3
    assert res.unit == "Wh"


def test_get_discharging_time(mock_load):
    mock_load.inst.query.return_value = "3600.0"
    res = mock_load.get_discharging_time()
    assert res.value == 3600.0
    assert res.unit == "s"


def test_shutdown_safety(mock_load):
    mock_load.shutdown_safety()
    mock_load.inst.write.assert_any_call(":SOUR:INP:STAT OFF")
