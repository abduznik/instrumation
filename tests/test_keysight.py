import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.keysight import KeysightInfiniiVision, Keysight34461A
from instrumation.results import MeasurementResult

@pytest.fixture
def mock_scope():
    with patch('pyvisa.ResourceManager'):
        driver = KeysightInfiniiVision("TCPIP::1.2.3.4::INSTR")
        driver.inst = MagicMock()
        # Ensure *OPC? returns 1 to avoid wait_ready timeouts
        driver.inst.query.return_value = "1"
        # This double doesn't model the SCPI error queue
        driver.check_errors_enabled = False
        yield driver

def test_scope_run_stop(mock_scope):
    mock_scope.run()
    mock_scope.inst.write.assert_any_call(":RUN")
    mock_scope.stop()
    mock_scope.inst.write.assert_any_call(":STOP")

def test_scope_measurements(mock_scope):
    mock_scope.inst.query.return_value = "1.234e6"
    res = mock_scope.measure_frequency(1)
    assert res.value == 1.234e6
    assert res.unit == "Hz"
    mock_scope.inst.query.assert_any_call(":MEASure:FREQuency? CHANnel1")

def test_scope_waveform_scaling(mock_scope):
    # Mock preamble: format, type, points, count, xinc, xor, xref, yinc, yor, yref
    # We care about 7, 8, 9 (yinc, yor, yref)
    mock_scope.inst.query.return_value = "1,1,1000,1,1e-9,0,0,0.01,0.5,128"
    mock_scope.inst.query_binary_values.return_value = [128, 228] # mid and peak
    
    res = mock_scope.get_waveform(1)
    
    # Val1: ((128 - 128) * 0.01) + 0.5 = 0.5V
    # Val2: ((228 - 128) * 0.01) + 0.5 = 1.5V
    assert res.value[0] == pytest.approx(0.5)
    assert res.value[1] == pytest.approx(1.5)

def test_scope_autoscale(mock_scope):
    mock_scope.auto_scale()
    mock_scope.inst.write.assert_any_call(":AUToscale")


# ── Keysight 34461A DMM Tests ─────────────────────────────────

@pytest.fixture
def mock_34461a():
    with patch('pyvisa.ResourceManager'):
        driver = Keysight34461A("TCPIP::1.2.3.5::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        # This double doesn't model the SCPI error queue
        driver.check_errors_enabled = False
        yield driver

def test_34461a_measure_dcv(mock_34461a):
    mock_34461a.inst.query.return_value = "5.12345"
    res = mock_34461a.measure_voltage()
    assert res.value == 5.12345
    assert res.unit == "V"
    mock_34461a.inst.query.assert_any_call(":MEAS:VOLT:DC?")

def test_34461a_measure_acv(mock_34461a):
    mock_34461a.inst.query.return_value = "0.98765"
    res = mock_34461a.measure_voltage(ac=True)
    assert res.value == 0.98765
    assert res.unit == "V"
    mock_34461a.inst.query.assert_any_call(":MEAS:VOLT:AC?")

def test_34461a_measure_resistance(mock_34461a):
    mock_34461a.inst.query.return_value = "9998.5"
    res = mock_34461a.measure_resistance()
    assert res.value == 9998.5
    assert res.unit == "Ohm"
    mock_34461a.inst.query.assert_any_call(":MEAS:RES?")

def test_34461a_measure_resistance_4wire(mock_34461a):
    mock_34461a.inst.query.return_value = "9998.5"
    res = mock_34461a.measure_resistance(four_wire=True)
    assert res.value == 9998.5
    assert res.unit == "Ohm"
    mock_34461a.inst.query.assert_any_call(":MEAS:FRES?")

def test_34461a_measure_dci(mock_34461a):
    mock_34461a.inst.query.return_value = "0.05001"
    res = mock_34461a.measure_current()
    assert res.value == 0.05001
    assert res.unit == "A"

def test_34461a_measure_frequency(mock_34461a):
    mock_34461a.inst.query.return_value = "1000.0"
    res = mock_34461a.measure_frequency()
    assert res.value == 1000.0
    assert res.unit == "Hz"

def test_34461a_measure_period(mock_34461a):
    mock_34461a.inst.query.return_value = "0.001"
    res = mock_34461a.measure_period()
    assert res.value == 0.001
    assert res.unit == "s"

def test_34461a_measure_temperature(mock_34461a):
    mock_34461a.inst.query.return_value = "23.45"
    res = mock_34461a.measure_temperature()
    assert res.value == 23.45
    assert res.unit == "C"

def test_34461a_measure_capacitance(mock_34461a):
    mock_34461a.inst.query.return_value = "1.0e-6"
    res = mock_34461a.measure_capacitance()
    assert res.value == 1.0e-6
    assert res.unit == "F"

def test_34461a_measure_diode(mock_34461a):
    mock_34461a.inst.query.return_value = "0.6543"
    res = mock_34461a.measure_diode()
    assert res.value == 0.6543
    assert res.unit == "V"


# ── Keysight SG Vector / ARB Tests (GH #195) ────────────────────

from instrumation.drivers.keysight import KeysightSG

@pytest.fixture
def mock_sg():
    with patch('pyvisa.ResourceManager'):
        driver = KeysightSG("TCPIP::1.2.3.6::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        driver.check_errors_enabled = False
        yield driver

def test_sg_enable_iq_modulation(mock_sg):
    mock_sg.enable_iq_modulation(True)
    mock_sg.inst.write.assert_any_call(":IQ:STAT ON")
    mock_sg.enable_iq_modulation(False)
    mock_sg.inst.write.assert_any_call(":IQ:STAT OFF")

def test_sg_get_iq_modulation_state(mock_sg):
    mock_sg.inst.query.return_value = "1"
    assert mock_sg.get_iq_modulation_state() is True
    mock_sg.inst.query.return_value = "0"
    assert mock_sg.get_iq_modulation_state() is False

def test_sg_set_iq_source(mock_sg):
    mock_sg.set_iq_source("INT")
    mock_sg.inst.write.assert_any_call(":IQ:SOUR INT")
    mock_sg.set_iq_source("ARB")
    mock_sg.inst.write.assert_any_call(":IQ:SOUR ARB")

def test_sg_set_iq_source_invalid(mock_sg):
    with pytest.raises(ValueError):
        mock_sg.set_iq_source("INVALID")

def test_sg_load_arb_waveform_with_data(mock_sg):
    data = [0.1, 0.2, 0.3, 0.4]
    mock_sg.load_arb_waveform("TEST_WFM", data)
    mock_sg.inst.write.assert_any_call(':RAD:ARB:WAV "TEST_WFM"')
    mock_sg.inst.write.assert_any_call(":RAD:ARB:DATA 0.1,0.2,0.3,0.4")

def test_sg_load_arb_waveform_name_only(mock_sg):
    mock_sg.load_arb_waveform("EXISTING_WFM")
    mock_sg.inst.write.assert_any_call(':RAD:ARB:WAV "EXISTING_WFM"')

def test_sg_load_arb_odd_length_raises(mock_sg):
    with pytest.raises(ValueError, match="even"):
        mock_sg.load_arb_waveform("BAD", [0.1, 0.2, 0.3])

def test_sg_arb_sample_rate(mock_sg):
    mock_sg.set_arb_sample_rate(100e6)
    mock_sg.inst.write.assert_any_call(":RAD:ARB:SRAT 100000000.0")

def test_sg_start_stop_arb_playback(mock_sg):
    mock_sg.start_arb_playback()
    mock_sg.inst.write.assert_any_call(":RAD:ARB:STAT ON")
    mock_sg.inst.write.assert_any_call(":INIT:IMM")
    mock_sg.stop_arb_playback()
    mock_sg.inst.write.assert_any_call(":RAD:ARB:STAT OFF")
    mock_sg.inst.write.assert_any_call(":FREQ:MODE CW")

def test_sg_trigger_iq_calibration(mock_sg):
    mock_sg.trigger_iq_calibration()
    mock_sg.inst.write.assert_any_call(":CAL:IQ:EXEC")

def test_sg_set_iq_gain_imbalance(mock_sg):
    mock_sg.set_iq_gain_imbalance(0.5)
    mock_sg.inst.write.assert_any_call(":CAL:IQ:GAIN 0.5")

def test_sg_set_iq_phase_imbalance(mock_sg):
    mock_sg.set_iq_phase_imbalance(2.3)
    mock_sg.inst.write.assert_any_call(":CAL:IQ:PHAS 2.3")

def test_sg_list_arb_waveforms(mock_sg):
    mock_sg.inst.query.return_value = '"WFM1","WFM2","WFM3"'
    result = mock_sg.list_arb_waveforms()
    assert result == ["WFM1", "WFM2", "WFM3"]
