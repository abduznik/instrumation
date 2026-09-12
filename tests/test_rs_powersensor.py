import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.rs_powersensor import RohdeSchwarzNRPZ


@pytest.fixture
def mock_sensor():
    with patch('pyvisa.ResourceManager'):
        driver = RohdeSchwarzNRPZ("USB0::0x0AAD::0x0138::100001::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        driver.check_errors_enabled = False
        yield driver


def test_set_get_frequency(mock_sensor):
    mock_sensor.set_frequency(2.4e9)
    mock_sensor.inst.write.assert_any_call("SENS:FREQ 2400000000.0")
    mock_sensor.inst.query.return_value = "2400000000.0"
    assert mock_sensor.get_frequency() == 2400000000.0


def test_set_offset_and_state(mock_sensor):
    mock_sensor.set_offset(-3.0)
    mock_sensor.inst.write.assert_any_call("SENS:CORR:OFFS -3.0")
    mock_sensor.set_offset_state(True)
    mock_sensor.inst.write.assert_any_call("SENS:CORR:OFFS:STAT ON")


def test_set_duty_cycle_and_state(mock_sensor):
    mock_sensor.set_duty_cycle(10.0)
    mock_sensor.inst.write.assert_any_call("SENS:CORR:DCYC 10.0")
    mock_sensor.set_duty_cycle_state(True)
    mock_sensor.inst.write.assert_any_call("SENS:CORR:DCYC:STAT ON")


def test_set_sparameter_correction_state(mock_sensor):
    mock_sensor.set_sparameter_correction_state(True)
    mock_sensor.inst.write.assert_any_call("SENS:CORR:SPD:STAT ON")


def test_set_trigger_source(mock_sensor):
    mock_sensor.set_trigger_source("bus")
    mock_sensor.inst.write.assert_any_call("TRIG:SOUR BUS")


def test_set_trigger_source_invalid_raises(mock_sensor):
    with pytest.raises(ValueError):
        mock_sensor.set_trigger_source("BOGUS")


def test_zero(mock_sensor):
    mock_sensor.zero()
    mock_sensor.inst.write.assert_any_call("CAL:ZERO:AUTO ONCE")


def test_measure_power(mock_sensor):
    mock_sensor.inst.query.return_value = "-8.2"
    res = mock_sensor.measure_power()
    assert res.value == -8.2
    assert res.unit == "dBm"
    mock_sensor.inst.query.assert_any_call("FETC?")


def test_unsupported_measures_return_zero(mock_sensor):
    assert mock_sensor.measure_frequency().value == 0.0
    assert mock_sensor.measure_duty_cycle().value == 0.0
    assert mock_sensor.measure_v_peak_to_peak().value == 0.0
