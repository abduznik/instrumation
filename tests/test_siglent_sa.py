import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.siglent_sa import SiglentSSA3000X


@pytest.fixture
def mock_sa():
    with patch('pyvisa.ResourceManager'):
        driver = SiglentSSA3000X("TCPIP::1.2.3.21::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        driver.check_errors_enabled = False
        yield driver


def test_peak_search(mock_sa):
    mock_sa.peak_search()
    mock_sa.inst.write.assert_any_call(":CALC:MARK1:MAX")


def test_get_marker_amplitude(mock_sa):
    mock_sa.inst.query.return_value = "-20.5"
    res = mock_sa.get_marker_amplitude()
    assert res.value == -20.5
    assert res.unit == "dBm"
    mock_sa.inst.query.assert_any_call(":CALC:MARK1:Y?")


def test_set_get_center_freq(mock_sa):
    mock_sa.set_center_freq(1e9)
    mock_sa.inst.write.assert_any_call(":SENS:FREQ:CENT 1.000000 GHz")
    mock_sa.inst.query.return_value = "1000000000"
    assert mock_sa.get_center_freq() == 1000000000.0


def test_set_get_span(mock_sa):
    mock_sa.set_span(1e6)
    mock_sa.inst.write.assert_any_call(":SENS:FREQ:SPAN 1000000.0")
    mock_sa.inst.query.return_value = "1000000"
    assert mock_sa.get_span() == 1000000.0


def test_set_rbw_vbw(mock_sa):
    mock_sa.set_rbw(1e3)
    mock_sa.inst.write.assert_any_call(":SENS:BAND:RES 1000.0")
    mock_sa.set_vbw(1e3)
    mock_sa.inst.write.assert_any_call(":SENS:BAND:VID 1000.0")


def test_set_ref_level(mock_sa):
    mock_sa.set_ref_level(-10.0)
    mock_sa.inst.write.assert_any_call(":DISP:WIND:TRAC:Y:RLEV -10.0")


def test_get_trace_data(mock_sa):
    mock_sa.inst.query.return_value = "-10.0,-20.0,-30.0"
    res = mock_sa.get_trace_data()
    assert res.value == [-10.0, -20.0, -30.0]
    assert res.unit == "dBm"


def test_get_peak_value_helper(mock_sa):
    mock_sa.inst.query.return_value = "-5.0"
    res = mock_sa.get_peak_value()
    assert res.value == -5.0
    mock_sa.inst.write.assert_any_call(":CALC:MARK1:MAX")


def test_unsupported_measures_return_zero(mock_sa):
    assert mock_sa.measure_frequency().value == 0.0
    assert mock_sa.measure_duty_cycle().value == 0.0
    assert mock_sa.measure_v_peak_to_peak().value == 0.0
