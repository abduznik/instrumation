import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.keysight_powersensor import KeysightU2000


@pytest.fixture
def mock_sensor():
    with patch('pyvisa.ResourceManager'):
        driver = KeysightU2000("USB0::0x0957::0x2A18::MY12345::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        driver.check_errors_enabled = False
        yield driver


def test_set_get_frequency(mock_sensor):
    mock_sensor.set_frequency(1e9)
    mock_sensor.inst.write.assert_any_call("SENS:FREQ 1000000000.0")
    mock_sensor.inst.query.return_value = "1000000000.0"
    assert mock_sensor.get_frequency() == 1000000000.0


def test_set_power_unit(mock_sensor):
    mock_sensor.set_power_unit("dbm")
    mock_sensor.inst.write.assert_any_call("UNIT:POW DBM")
    mock_sensor.set_power_unit("w")
    mock_sensor.inst.write.assert_any_call("UNIT:POW W")


def test_set_power_unit_invalid_raises(mock_sensor):
    with pytest.raises(ValueError):
        mock_sensor.set_power_unit("BOGUS")


def test_set_gain_offset_state(mock_sensor):
    mock_sensor.set_gain_offset_state(True)
    mock_sensor.inst.write.assert_any_call("SENS:CORR:GAIN2:STAT ON")


def test_set_gain_offset(mock_sensor):
    mock_sensor.set_gain_offset(-10.0)
    mock_sensor.inst.write.assert_any_call("SENS:CORR:GAIN2 -10.0")


def test_zero(mock_sensor):
    mock_sensor.zero()
    mock_sensor.inst.write.assert_any_call("CAL:ZERO:TYPE INT")
    mock_sensor.inst.write.assert_any_call("CAL:ZERO:AUTO ONCE")


def test_measure_power(mock_sensor):
    mock_sensor.inst.query.return_value = "-15.3"
    res = mock_sensor.measure_power()
    assert res.value == -15.3
    assert res.unit == "dBm"
    mock_sensor.inst.query.assert_any_call("FETC?")


def test_unsupported_measures_return_zero(mock_sensor):
    assert mock_sensor.measure_frequency().value == 0.0
    assert mock_sensor.measure_duty_cycle().value == 0.0
    assert mock_sensor.measure_v_peak_to_peak().value == 0.0
