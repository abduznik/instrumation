import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.keysight_ac_psu import KeysightAC6800B


@pytest.fixture
def mock_psu():
    with patch('pyvisa.ResourceManager'):
        driver = KeysightAC6800B("TCPIP::10.0.0.60::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "0"
        driver.check_errors_enabled = False
        yield driver


def test_set_voltage(mock_psu):
    mock_psu.set_voltage(120.0)
    mock_psu.inst.write.assert_any_call("SOUR:VOLT 120.0")


def test_get_voltage(mock_psu):
    mock_psu.inst.query.return_value = "120.0"
    assert mock_psu.get_voltage() == 120.0


def test_set_frequency(mock_psu):
    mock_psu.set_frequency(60.0)
    mock_psu.inst.write.assert_any_call("SOUR:FREQ 60.0")


def test_get_frequency(mock_psu):
    mock_psu.inst.query.return_value = "60.0"
    assert mock_psu.get_frequency() == 60.0


def test_set_output_mode(mock_psu):
    mock_psu.set_output_mode("ac+dc")
    mock_psu.inst.write.assert_any_call("SOUR:VOLT:MODE AC+DC")


def test_set_output_mode_alias(mock_psu):
    mock_psu.set_output_mode("ACDC")
    mock_psu.inst.write.assert_any_call("SOUR:VOLT:MODE AC+DC")


def test_set_output_mode_invalid_raises(mock_psu):
    with pytest.raises(ValueError):
        mock_psu.set_output_mode("BOGUS")


def test_get_output_mode(mock_psu):
    mock_psu.inst.query.return_value = "AC"
    assert mock_psu.get_output_mode() == "AC"


def test_set_output_on_off(mock_psu):
    mock_psu.set_output(True)
    mock_psu.inst.write.assert_any_call("OUTP ON")
    mock_psu.set_output(False)
    mock_psu.inst.write.assert_any_call("OUTP OFF")


def test_get_output(mock_psu):
    mock_psu.inst.query.return_value = "1"
    assert mock_psu.get_output() is True


def test_measure_voltage(mock_psu):
    mock_psu.inst.query.return_value = "119.8"
    res = mock_psu.measure_voltage()
    assert res.value == 119.8
    assert res.unit == "Vrms"
    mock_psu.inst.query.assert_any_call("MEAS:VOLT:AC?")


def test_measure_current(mock_psu):
    mock_psu.inst.query.return_value = "1.5"
    res = mock_psu.measure_current()
    assert res.value == 1.5
    assert res.unit == "Arms"
    mock_psu.inst.query.assert_any_call("MEAS:CURR:AC?")


def test_measure_power(mock_psu):
    mock_psu.inst.query.return_value = "150.0"
    res = mock_psu.measure_power()
    assert res.value == 150.0
    assert res.unit == "W"
    mock_psu.inst.query.assert_any_call("MEAS:POW:AC?")


def test_set_current_limit(mock_psu):
    mock_psu.set_current_limit(10.0)
    mock_psu.inst.write.assert_any_call("SOUR:CURR 10.0")


def test_get_current_limit(mock_psu):
    mock_psu.inst.query.return_value = "10.0"
    assert mock_psu.get_current_limit() == 10.0


def test_set_ovp(mock_psu):
    mock_psu.set_ovp(150.0)
    mock_psu.inst.write.assert_any_call("SOUR:VOLT:PROT 150.0")


def test_set_ocp(mock_psu):
    mock_psu.set_ocp(15.0)
    mock_psu.inst.write.assert_any_call("SOUR:CURR:PROT 15.0")


def test_clear_protection(mock_psu):
    mock_psu.clear_protection()
    mock_psu.inst.write.assert_any_call("OUTP:PROT:CLE")


def test_set_dc_offset(mock_psu):
    mock_psu.set_dc_offset(5.0)
    mock_psu.inst.write.assert_any_call("SOUR:VOLT:OFFS 5.0")


def test_get_dc_offset(mock_psu):
    mock_psu.inst.query.return_value = "5.0"
    assert mock_psu.get_dc_offset() == 5.0


def test_shutdown_safety(mock_psu):
    mock_psu.shutdown_safety()
    mock_psu.inst.write.assert_any_call("OUTP OFF")
    mock_psu.inst.write.assert_any_call("SOUR:VOLT 0.0")
