import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.tektronix_pa1000 import TektronixPA1000


@pytest.fixture
def mock_analyzer():
    with patch('pyvisa.ResourceManager'), patch('time.sleep'):
        driver = TektronixPA1000("TCPIP::1.2.3.40::5025::SOCKET")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        driver.check_errors_enabled = False
        yield driver


def test_preset_uses_reset_delay(mock_analyzer):
    with patch('time.sleep') as mock_sleep:
        mock_analyzer.preset()
        mock_analyzer.inst.write.assert_any_call("*RST")
        mock_sleep.assert_any_call(5.0)


def test_wait_ready_sleeps_fixed_delay(mock_analyzer):
    with patch('time.sleep') as mock_sleep:
        mock_analyzer.wait_ready()
        mock_sleep.assert_any_call(0.5)


def test_clear_selection(mock_analyzer):
    mock_analyzer.clear_selection()
    mock_analyzer.inst.write.assert_any_call(":SEL:CLR")


def test_select_voltage_current_power_frequency_pf(mock_analyzer):
    mock_analyzer.select_voltage()
    mock_analyzer.inst.write.assert_any_call(":SEL:VLT")
    mock_analyzer.select_current()
    mock_analyzer.inst.write.assert_any_call(":SEL:CURR")
    mock_analyzer.select_power()
    mock_analyzer.inst.write.assert_any_call(":SEL:PWR")
    mock_analyzer.select_frequency()
    mock_analyzer.inst.write.assert_any_call(":SEL:FRQ")
    mock_analyzer.select_power_factor()
    mock_analyzer.inst.write.assert_any_call(":SEL:PWRF")


def test_set_auto_range(mock_analyzer):
    mock_analyzer.set_auto_range_voltage()
    mock_analyzer.inst.write.assert_any_call(":RNG:VLT AUT")
    mock_analyzer.set_auto_range_current()
    mock_analyzer.inst.write.assert_any_call(":RNG:CURR AUT")


def test_set_auto_zero(mock_analyzer):
    mock_analyzer.set_auto_zero(True)
    mock_analyzer.inst.write.assert_any_call(":SYST:ZERO 1")
    mock_analyzer.set_auto_zero(False)
    mock_analyzer.inst.write.assert_any_call(":SYST:ZERO 0")


def test_get_reading_list(mock_analyzer):
    mock_analyzer.inst.query.return_value = "VLT,CURR"
    assert mock_analyzer.get_reading_list() == "VLT,CURR"
    mock_analyzer.inst.query.assert_any_call(":FRF?")


def test_get_data_status(mock_analyzer):
    mock_analyzer.inst.query.return_value = "0"
    assert mock_analyzer.get_data_status() == "0"
    mock_analyzer.inst.query.assert_any_call(":DSR?")


def test_fetch_readings(mock_analyzer):
    mock_analyzer.inst.query.return_value = "120.5,1.2"
    res = mock_analyzer.fetch_readings()
    assert res.value == [120.5, 1.2]
    mock_analyzer.inst.query.assert_any_call(":FRD?")


def test_measure_voltage_rms(mock_analyzer):
    mock_analyzer.inst.query.return_value = "120.5"
    res = mock_analyzer.measure_voltage_rms()
    assert res.value == 120.5
    assert res.unit == "V"
    mock_analyzer.inst.write.assert_any_call(":SEL:CLR")
    mock_analyzer.inst.write.assert_any_call(":SEL:VLT")


def test_measure_current_rms(mock_analyzer):
    mock_analyzer.inst.query.return_value = "1.234"
    res = mock_analyzer.measure_current_rms()
    assert res.value == 1.234
    assert res.unit == "A"


def test_measure_active_power(mock_analyzer):
    mock_analyzer.inst.query.return_value = "144.6"
    res = mock_analyzer.measure_active_power()
    assert res.value == 144.6
    assert res.unit == "W"


def test_measure_frequency(mock_analyzer):
    mock_analyzer.inst.query.return_value = "60.0"
    res = mock_analyzer.measure_frequency()
    assert res.value == 60.0
    assert res.unit == "Hz"


def test_measure_returns_zero_when_empty(mock_analyzer):
    mock_analyzer.inst.query.return_value = ""
    res = mock_analyzer.measure_voltage_rms()
    assert res.value == 0.0


def test_unsupported_measures_return_zero(mock_analyzer):
    assert mock_analyzer.measure_duty_cycle().value == 0.0
    assert mock_analyzer.measure_v_peak_to_peak().value == 0.0
