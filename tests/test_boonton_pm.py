import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.boonton_pm import Boonton4531, Boonton4532


@pytest.fixture
def mock_pm():
    with patch('pyvisa.ResourceManager'):
        driver = Boonton4531("GPIB0::13::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "0"
        driver.check_errors_enabled = False
        yield driver


@pytest.fixture
def mock_pm2():
    with patch('pyvisa.ResourceManager'):
        driver = Boonton4532("GPIB0::14::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "0"
        driver.check_errors_enabled = False
        yield driver


def test_set_frequency(mock_pm):
    mock_pm.set_frequency(1e9)
    mock_pm.inst.write.assert_any_call("FREQ 1000000000.0")


def test_get_frequency(mock_pm):
    mock_pm.inst.query.return_value = "1000000000.0"
    assert mock_pm.get_frequency() == 1e9


def test_set_power_unit(mock_pm):
    mock_pm.set_power_unit("dbm")
    mock_pm.inst.write.assert_any_call("UNIT:POWER DBM")


def test_set_power_unit_invalid_raises(mock_pm):
    with pytest.raises(ValueError):
        mock_pm.set_power_unit("BOGUS")


def test_set_offset(mock_pm):
    mock_pm.set_offset(3.0)
    mock_pm.inst.write.assert_any_call("CAL1:OFFSET 3.0")


def test_get_offset(mock_pm):
    mock_pm.inst.query.return_value = "3.0"
    assert mock_pm.get_offset() == 3.0


def test_measure_power(mock_pm):
    mock_pm.inst.query.return_value = "-10.5"
    res = mock_pm.measure_power()
    assert res.value == -10.5
    assert res.unit == "dBm"
    mock_pm.inst.query.assert_any_call("MEAS:POWER?")


def test_measure_peak_power(mock_pm):
    mock_pm.inst.query.return_value = "-2.3"
    res = mock_pm.measure_peak_power()
    assert res.value == -2.3
    mock_pm.inst.query.assert_any_call("MEAS:PEAK?")


def test_set_video_bandwidth(mock_pm):
    mock_pm.set_video_bandwidth(4e6)
    mock_pm.inst.write.assert_any_call("SENS:BAND:VIDEO 4000000.0")


def test_get_video_bandwidth(mock_pm):
    mock_pm.inst.query.return_value = "4000000.0"
    assert mock_pm.get_video_bandwidth() == 4e6


def test_set_trigger_source(mock_pm):
    mock_pm.set_trigger_source("internal")
    mock_pm.inst.write.assert_any_call("TRIG:SOURCE INT")


def test_set_trigger_source_invalid_raises(mock_pm):
    with pytest.raises(ValueError):
        mock_pm.set_trigger_source("BOGUS")


def test_set_trigger_level(mock_pm):
    mock_pm.set_trigger_level(-20.0)
    mock_pm.inst.write.assert_any_call("TRIG:LEVEL -20.0")


def test_measure_pulse_width(mock_pm):
    mock_pm.inst.query.return_value = "0.000001"
    res = mock_pm.measure_pulse_width()
    assert res.value == 1e-6
    assert res.unit == "s"


def test_zero(mock_pm):
    mock_pm.inst.query.return_value = "1"
    mock_pm.zero()
    mock_pm.inst.write.assert_any_call("CAL:ZERO")


def test_shutdown_safety(mock_pm):
    mock_pm.shutdown_safety()
    mock_pm.inst.write.assert_any_call("*CLS")


def test_boonton4532_measure_power_channel1(mock_pm2):
    mock_pm2.inst.query.return_value = "-8.0"
    res = mock_pm2.measure_power()
    assert res.value == -8.0
    assert res.channel == 1
    mock_pm2.inst.query.assert_any_call("MEAS:POWER?")


def test_boonton4532_measure_power_channel2(mock_pm2):
    mock_pm2.inst.query.return_value = "-9.0"
    res = mock_pm2.measure_power(channel=2)
    assert res.value == -9.0
    assert res.channel == 2
    mock_pm2.inst.query.assert_any_call("MEAS:POWER? 2")


def test_boonton4532_measure_peak_power_channel2(mock_pm2):
    mock_pm2.inst.query.return_value = "-1.0"
    res = mock_pm2.measure_peak_power(channel=2)
    assert res.value == -1.0
    mock_pm2.inst.query.assert_any_call("MEAS:PEAK? 2")
