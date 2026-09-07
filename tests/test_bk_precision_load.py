import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.bk_precision import BKPrecision8600


@pytest.fixture
def mock_load():
    with patch('pyvisa.ResourceManager'):
        driver = BKPrecision8600("TCPIP::1.2.3.8::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        # This double doesn't model the SCPI error queue
        driver.check_errors_enabled = False
        yield driver


def test_set_mode_valid(mock_load):
    mock_load.set_mode("cc")
    mock_load.inst.write.assert_any_call(":SOUR:FUNC CURR")
    mock_load.set_mode("CV")
    mock_load.inst.write.assert_any_call(":SOUR:FUNC VOLT")
    mock_load.set_mode("cr")
    mock_load.inst.write.assert_any_call(":SOUR:FUNC RES")
    mock_load.set_mode("CP")
    mock_load.inst.write.assert_any_call(":SOUR:FUNC POW")


def test_set_mode_invalid_raises(mock_load):
    with pytest.raises(ValueError):
        mock_load.set_mode("XX")


def test_get_mode(mock_load):
    mock_load.inst.query.return_value = "CURR"
    assert mock_load.get_mode() == "CC"
    mock_load.inst.query.return_value = "RES"
    assert mock_load.get_mode() == "CR"


def test_set_get_current(mock_load):
    mock_load.set_current(2.5)
    mock_load.inst.write.assert_any_call(":SOUR:CURR:LEV:IMM 2.5")
    mock_load.inst.query.return_value = "2.5"
    assert mock_load.get_current() == 2.5


def test_set_get_voltage(mock_load):
    mock_load.set_voltage(12.0)
    mock_load.inst.write.assert_any_call(":SOUR:VOLT:LEV:IMM 12.0")
    mock_load.inst.query.return_value = "12.0"
    assert mock_load.get_voltage() == 12.0


def test_set_get_resistance(mock_load):
    mock_load.set_resistance(100.0)
    mock_load.inst.write.assert_any_call(":SOUR:RES:LEV:IMM 100.0")
    mock_load.inst.query.return_value = "100.0"
    assert mock_load.get_resistance() == 100.0


def test_set_get_power(mock_load):
    mock_load.set_power(50.0)
    mock_load.inst.write.assert_any_call(":SOUR:POW:LEV:IMM 50.0")
    mock_load.inst.query.return_value = "50.0"
    assert mock_load.get_power() == 50.0


def test_set_get_input(mock_load):
    mock_load.set_input(True)
    mock_load.inst.write.assert_any_call(":SOUR:INP:STAT ON")
    mock_load.inst.query.return_value = "ON"
    assert mock_load.get_input() is True
    mock_load.set_input(False)
    mock_load.inst.write.assert_any_call(":SOUR:INP:STAT OFF")


def test_measure_voltage_current_power(mock_load):
    mock_load.inst.query.return_value = "4.999"
    res = mock_load.measure_voltage()
    assert res.value == 4.999 and res.unit == "V"

    mock_load.inst.query.return_value = "1.001"
    res = mock_load.measure_current()
    assert res.value == 1.001 and res.unit == "A"

    mock_load.inst.query.return_value = "5.0"
    res = mock_load.measure_power()
    assert res.value == 5.0 and res.unit == "W"


def test_protection_setpoints(mock_load):
    mock_load.set_ovp(30.0)
    mock_load.inst.write.assert_any_call(":SOUR:VOLT:PROT 30.0")
    mock_load.set_ocp(5.0)
    mock_load.inst.write.assert_any_call(":SOUR:CURR:PROT 5.0")
    mock_load.set_opp(100.0)
    mock_load.inst.write.assert_any_call(":SOUR:POW:PROT 100.0")


def test_clear_protection(mock_load):
    mock_load.clear_protection()
    mock_load.inst.write.assert_any_call(":SOUR:PROT:CLE")


def test_battery_test_mode(mock_load):
    mock_load.set_battery_test_mode(True)
    mock_load.inst.write.assert_any_call(":SOUR:BATT:MODE ON")
    mock_load.set_battery_cutoff_voltage(9.0)
    mock_load.inst.write.assert_any_call(":SOUR:BATT:LEV:VOLT 9.0")


def test_battery_test_capacity(mock_load):
    mock_load.inst.query.return_value = "1.234"
    res = mock_load.get_battery_test_capacity()
    assert res.value == 1.234
    assert res.unit == "Ah"


def test_shutdown_safety(mock_load):
    mock_load.shutdown_safety()
    mock_load.inst.write.assert_any_call(":SOUR:INP:STAT OFF")
