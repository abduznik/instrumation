import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.siglent_scope import SiglentSDS2000XPlus


@pytest.fixture
def mock_scope():
    with patch('pyvisa.ResourceManager'):
        driver = SiglentSDS2000XPlus("TCPIP::1.2.3.19::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        driver.check_errors_enabled = False
        yield driver


def test_run(mock_scope):
    mock_scope.run()
    mock_scope.inst.write.assert_any_call(":TRIG:RUN")


def test_stop(mock_scope):
    mock_scope.stop()
    mock_scope.inst.write.assert_any_call(":TRIG:STOP")


def test_single(mock_scope):
    mock_scope.single()
    mock_scope.inst.write.assert_any_call(":TRIG:MODE SINGLE")


def test_get_waveform(mock_scope):
    mock_scope.inst.query_binary_values.return_value = [1.0, 2.0, 3.0]
    res = mock_scope.get_waveform(1)
    assert res.value == [1.0, 2.0, 3.0]
    assert res.unit == "V"
    mock_scope.inst.write.assert_any_call(":WAV:SOUR C1")


def test_auto_scale(mock_scope):
    mock_scope.auto_scale()
    mock_scope.inst.write.assert_any_call(":AUT")


def test_set_trigger(mock_scope):
    mock_scope.set_trigger("C1", 1.5, "RISING")
    mock_scope.inst.write.assert_any_call(":TRIG:EDGE:SOUR C1")
    mock_scope.inst.write.assert_any_call(":TRIG:EDGE:LEV 1.5")
    mock_scope.inst.write.assert_any_call(":TRIG:EDGE:SLOP RISING")


def test_get_screenshot(mock_scope):
    mock_scope.inst.read_raw.return_value = b"\x89PNG..."
    data = mock_scope.get_screenshot()
    assert data == b"\x89PNG..."
    mock_scope.inst.write.assert_any_call(":PRIN? PNG")


def test_measure_frequency(mock_scope):
    mock_scope.inst.query.return_value = "1000.5"
    res = mock_scope.measure_frequency(channel=1)
    assert res.value == 1000.5
    assert res.unit == "Hz"
    mock_scope.inst.write.assert_any_call(":MEAS:SIMP:SOUR C1")
    mock_scope.inst.query.assert_any_call(":MEAS:SIMP:VAL? FREQ")


def test_measure_duty_cycle(mock_scope):
    mock_scope.inst.query.return_value = "45.0"
    res = mock_scope.measure_duty_cycle(channel=2)
    assert res.value == 45.0
    assert res.unit == "%"
    mock_scope.inst.write.assert_any_call(":MEAS:SIMP:SOUR C2")


def test_measure_v_peak_to_peak(mock_scope):
    mock_scope.inst.query.return_value = "3.3"
    res = mock_scope.measure_v_peak_to_peak(channel=1)
    assert res.value == 3.3
    assert res.unit == "V"


def test_measure_returns_zero_on_parse_error(mock_scope):
    mock_scope.inst.query.return_value = "NOT_A_NUMBER"
    res = mock_scope.measure_frequency(channel=1)
    assert res.value == 0.0


def test_shutdown_safety(mock_scope):
    mock_scope.shutdown_safety()
    mock_scope.inst.write.assert_any_call(":TRIG:STOP")
