import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.rigol_mso5000 import RigolMSO5000


@pytest.fixture
def mock_scope():
    with patch('pyvisa.ResourceManager'):
        driver = RigolMSO5000("TCPIP::1.2.3.20::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        driver.check_errors_enabled = False
        yield driver


def test_run_stop_single(mock_scope):
    mock_scope.run()
    mock_scope.inst.write.assert_any_call(":RUN")
    mock_scope.stop()
    mock_scope.inst.write.assert_any_call(":STOP")
    mock_scope.single()
    mock_scope.inst.write.assert_any_call(":SINGle")


def test_auto_scale(mock_scope):
    mock_scope.auto_scale()
    mock_scope.inst.write.assert_any_call(":AUTOscale")


def test_set_trigger(mock_scope):
    mock_scope.set_trigger("CHANnel1", 1.2, "POSITIVE")
    mock_scope.inst.write.assert_any_call(":TRIGger:MODE EDGE")
    mock_scope.inst.write.assert_any_call(":TRIGger:EDGE:SOURce CHANnel1")
    mock_scope.inst.write.assert_any_call(":TRIGger:EDGE:LEVel 1.2")
    mock_scope.inst.write.assert_any_call(":TRIGger:EDGE:SLOPe POSitive")


def test_get_waveform(mock_scope):
    mock_scope.inst.query_binary_values.return_value = [1, 2, 3]
    res = mock_scope.get_waveform(2)
    assert res.value == [1.0, 2.0, 3.0]
    assert res.unit == "V"
    mock_scope.inst.write.assert_any_call(":WAVeform:SOURce CHANnel2")


def test_get_screenshot(mock_scope):
    mock_scope.inst.read_raw.return_value = b"\x89PNG..."
    data = mock_scope.get_screenshot()
    assert data == b"\x89PNG..."
    mock_scope.inst.write.assert_any_call(":DISPlay:DATA? PNG,COLor")


def test_measure_frequency(mock_scope):
    mock_scope.inst.query.return_value = "1.0E+3"
    res = mock_scope.measure_frequency(channel=1)
    assert res.value == 1000.0
    assert res.unit == "Hz"
    mock_scope.inst.query.assert_any_call(":MEASure:ITEM? FREQuency,CHANnel1")


def test_measure_duty_cycle(mock_scope):
    mock_scope.inst.query.return_value = "5.0E+1"
    res = mock_scope.measure_duty_cycle(channel=2)
    assert res.value == 50.0
    assert res.unit == "%"
    mock_scope.inst.query.assert_any_call(":MEASure:ITEM? PDUTy,CHANnel2")


def test_measure_v_peak_to_peak(mock_scope):
    mock_scope.inst.query.return_value = "3.3E+0"
    res = mock_scope.measure_v_peak_to_peak(channel=1)
    assert res.value == 3.3
    assert res.unit == "V"


def test_measure_returns_zero_on_parse_error(mock_scope):
    mock_scope.inst.query.return_value = "GARBAGE"
    res = mock_scope.measure_frequency(channel=1)
    assert res.value == 0.0


def test_shutdown_safety(mock_scope):
    mock_scope.shutdown_safety()
    mock_scope.inst.write.assert_any_call(":STOP")
