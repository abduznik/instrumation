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


# Every expected command below comes from the 4530 Series Instruction
# Manual, Table 4-1 "Remote Command Summary". The 4530 defines no FREQ,
# UNIT:POWER, SENS:BAND:VIDEO, CAL1:OFFSET, MEAS:PEAK? or
# MEAS:PULSE:WIDTH? command.

def test_set_frequency_uses_sense_correction_in_ghz(mock_pm):
    mock_pm.set_frequency(1.5e9)
    mock_pm.inst.write.assert_any_call("SENS:CORR:FREQ 1.5 GHz")


def test_get_frequency_converts_ghz_to_hz(mock_pm):
    mock_pm.inst.query.return_value = "1.5"
    assert mock_pm.get_frequency() == 1.5e9


def test_set_power_unit_dbm(mock_pm):
    mock_pm.set_power_unit("dbm")
    mock_pm.inst.write.assert_any_call("CALC:UNIT DBM")


def test_set_power_unit_watts(mock_pm):
    mock_pm.set_power_unit("W")
    mock_pm.inst.write.assert_any_call("CALC:UNIT WATTS")


def test_set_power_unit_invalid_raises(mock_pm):
    with pytest.raises(ValueError):
        mock_pm.set_power_unit("BOGUS")


def test_set_offset(mock_pm):
    mock_pm.set_offset(3.0)
    mock_pm.inst.write.assert_any_call("SENS:CORR:OFF 3.0")


def test_get_offset(mock_pm):
    mock_pm.inst.query.return_value = "3.0"
    assert mock_pm.get_offset() == 3.0
    mock_pm.inst.query.assert_any_call("SENS:CORR:OFF?")


def test_measure_power(mock_pm):
    mock_pm.inst.query.return_value = "-10.5"
    res = mock_pm.measure_power()
    assert res.value == -10.5
    assert res.unit == "dBm"
    mock_pm.inst.query.assert_any_call("MEAS:POW?")


def test_measure_peak_power_reads_first_field_of_pulse_array(mock_pm):
    # FETCh:ARRay:AMEAsure:POWer? -> PulseOnPeak, PulseCycleAvg, ...
    mock_pm.inst.query.return_value = "-2.3,4.0,3.5,5.0,4.8,0.5"
    res = mock_pm.measure_peak_power()
    assert res.value == -2.3
    assert res.unit == "dBm"
    mock_pm.inst.query.assert_any_call("FETC:ARR:AMEA:POW?")


def test_set_video_bandwidth_selects_high_low(mock_pm):
    mock_pm.set_video_bandwidth("LOW")
    mock_pm.inst.write.assert_any_call("SENS:BAND LOW")


def test_set_video_bandwidth_rejects_numeric_hz(mock_pm):
    with pytest.raises(ValueError):
        mock_pm.set_video_bandwidth(4e6)


def test_get_video_bandwidth(mock_pm):
    mock_pm.inst.query.return_value = "HIGH"
    assert mock_pm.get_video_bandwidth() == "HIGH"
    mock_pm.inst.query.assert_any_call("SENS:BAND?")


def test_set_trigger_source_maps_to_manual_arguments(mock_pm):
    mock_pm.set_trigger_source("internal")
    mock_pm.inst.write.assert_any_call("TRIG:SOUR SENSOR1")
    mock_pm.set_trigger_source("external")
    mock_pm.inst.write.assert_any_call("TRIG:SOUR EXTERNAL")
    mock_pm.set_trigger_source("free_run")
    mock_pm.inst.write.assert_any_call("TRIG:SOUR IMMEDIATE")


def test_set_trigger_source_invalid_raises(mock_pm):
    with pytest.raises(ValueError):
        mock_pm.set_trigger_source("BOGUS")


def test_set_trigger_level(mock_pm):
    mock_pm.set_trigger_level(-20.0)
    mock_pm.inst.write.assert_any_call("TRIG:LEV -20.0")


def test_measure_pulse_width_reads_third_field_of_timing_array(mock_pm):
    # PulseFreq, PulsePeriod, PulseWidth, Offtime, DutyCycle, Risetime, Falltime
    mock_pm.inst.query.return_value = "1.0E+03,1.0E-03,1.0E-06,9.99E-04,0.1,1e-8,1e-8"
    res = mock_pm.measure_pulse_width()
    assert res.value == 1e-6
    assert res.unit == "s"
    mock_pm.inst.query.assert_any_call("FETC:ARR:AMEA:TIM?")


def test_zero_uses_internal_calibrator(mock_pm):
    mock_pm.inst.query.return_value = "1"
    mock_pm.zero()
    mock_pm.inst.write.assert_any_call("CAL:INT:ZERO")


def test_shutdown_safety(mock_pm):
    mock_pm.shutdown_safety()
    mock_pm.inst.write.assert_any_call("*CLS")


def test_boonton4532_measure_power_channel1(mock_pm2):
    mock_pm2.inst.query.return_value = "-8.0"
    res = mock_pm2.measure_power()
    assert res.value == -8.0
    assert res.channel == 1
    mock_pm2.inst.query.assert_any_call("MEAS:POW?")


def test_boonton4532_measure_power_channel2_uses_suffix(mock_pm2):
    mock_pm2.inst.query.return_value = "-9.0"
    res = mock_pm2.measure_power(channel=2)
    assert res.value == -9.0
    assert res.channel == 2
    mock_pm2.inst.query.assert_any_call("MEAS2:POW?")


def test_boonton4532_measure_peak_power_channel2_uses_suffix(mock_pm2):
    mock_pm2.inst.query.return_value = "-1.0,0,0,0,0,0"
    res = mock_pm2.measure_peak_power(channel=2)
    assert res.value == -1.0
    mock_pm2.inst.query.assert_any_call("FETC2:ARR:AMEA:POW?")
