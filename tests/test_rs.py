import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.rs import RohdeSchwarzSG, RohdeSchwarzSA
from instrumation.results import MeasurementResult


@pytest.fixture
def mock_sg():
    with patch('pyvisa.ResourceManager'):
        driver = RohdeSchwarzSG("TCPIP::192.168.1.10::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        yield driver


@pytest.fixture
def mock_sa():
    with patch('pyvisa.ResourceManager'):
        driver = RohdeSchwarzSA("TCPIP::192.168.1.11::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        yield driver


# ── RohdeSchwarzSG Tests ──────────────────────────────────────

def test_sg_preset_sends_rst(mock_sg):
    mock_sg.preset()
    mock_sg.inst.write.assert_any_call("*RST")

def test_sg_preset_disables_display(mock_sg):
    mock_sg.preset(automation_optimized=True)
    mock_sg.inst.write.assert_any_call(":SYST:DISP:UPD OFF")

def test_sg_preset_no_display_off_when_not_optimized(mock_sg):
    mock_sg.preset(automation_optimized=False)
    calls = [str(c) for c in mock_sg.inst.write.call_args_list]
    assert not any(":SYST:DISP:UPD OFF" in c for c in calls)

def test_sg_set_frequency(mock_sg):
    mock_sg.set_frequency(1e9)
    mock_sg.inst.write.assert_any_call(":FREQ 1.000000 GHz")

def test_sg_set_amplitude(mock_sg):
    mock_sg.set_amplitude(-10.0)
    mock_sg.inst.write.assert_any_call(":POW -10.00 DBM")

def test_sg_set_output_on(mock_sg):
    mock_sg.set_output(True)
    mock_sg.inst.write.assert_any_call(":OUTP ON")

def test_sg_set_output_off(mock_sg):
    mock_sg.set_output(False)
    mock_sg.inst.write.assert_any_call(":OUTP OFF")

def test_sg_set_mod_state_am(mock_sg):
    mock_sg.set_mod_state("AM", True)
    mock_sg.inst.write.assert_any_call(":AM:STAT ON")

def test_sg_set_mod_state_fm(mock_sg):
    mock_sg.set_mod_state("FM", False)
    mock_sg.inst.write.assert_any_call(":FM:STAT OFF")

def test_sg_set_mod_state_pulse(mock_sg):
    mock_sg.set_mod_state("PULSE", True)
    mock_sg.inst.write.assert_any_call(":PULM:STAT ON")

def test_sg_set_mod_state_pulm_alias(mock_sg):
    mock_sg.set_mod_state("PULM", False)
    mock_sg.inst.write.assert_any_call(":PULM:STAT OFF")

def test_sg_start_sweep(mock_sg):
    mock_sg.start_sweep(start=1e9, stop=2e9, points=101, dwell=0.001)
    mock_sg.inst.write.assert_any_call(":FREQ:STAR 1000000000.0")
    mock_sg.inst.write.assert_any_call(":FREQ:STOP 2000000000.0")
    mock_sg.inst.write.assert_any_call(":SWE:POIN 101")
    mock_sg.inst.write.assert_any_call(":FREQ:MODE SWE")

def test_sg_configure_list_sweep(mock_sg):
    freqs = [1e9, 2e9, 3e9]
    powers = [-10.0, -20.0, -30.0]
    mock_sg.configure_list_sweep(freqs, powers)
    mock_sg.inst.write.assert_any_call(":LIST:FREQ 1000000000.0,2000000000.0,3000000000.0")
    mock_sg.inst.write.assert_any_call(":LIST:POW -10.0,-20.0,-30.0")
    mock_sg.inst.write.assert_any_call(":FREQ:MODE LIST")


# ── RohdeSchwarzSA Tests ──────────────────────────────────────

def test_sa_preset_sends_rst(mock_sa):
    mock_sa.preset()
    mock_sa.inst.write.assert_any_call("*RST")

def test_sa_set_center_freq(mock_sa):
    mock_sa.set_center_freq(2.4e9)
    mock_sa.inst.write.assert_any_call(":FREQ:CENT 2.400000 GHz")

def test_sa_set_span(mock_sa):
    mock_sa.set_span(100e6)
    mock_sa.inst.write.assert_any_call(":FREQ:SPAN 100.000000 MHz")

def test_sa_set_rbw(mock_sa):
    mock_sa.set_rbw(1e6)
    mock_sa.inst.write.assert_any_call(":BAND 1.000000 MHz")

def test_sa_set_vbw(mock_sa):
    mock_sa.set_vbw(100e3)
    mock_sa.inst.write.assert_any_call(":BAND:VID 100.000000 kHz")

def test_sa_peak_search(mock_sa):
    mock_sa.peak_search()
    mock_sa.inst.write.assert_any_call(":CALC:MARK1:MAX")

def test_sa_get_marker_amplitude(mock_sa):
    mock_sa.inst.query.return_value = "-45.3"
    result = mock_sa.get_marker_amplitude()
    assert isinstance(result, MeasurementResult)
    assert result.value == pytest.approx(-45.3)
    assert result.unit == "dBm"
    mock_sa.inst.query.assert_any_call(":CALC:MARK1:Y?")

def test_sa_get_trace_data_configures_binary_format(mock_sa):
    mock_sa.inst.query_binary_values.return_value = [-10.0, -20.0, -30.0]
    result = mock_sa.get_trace_data()
    mock_sa.inst.write.assert_any_call(":FORM REAL,32")
    mock_sa.inst.write.assert_any_call(":INIT:CONT OFF")
    assert isinstance(result, MeasurementResult)
    assert result.unit == "dBm"
    assert result.value == [-10.0, -20.0, -30.0]
