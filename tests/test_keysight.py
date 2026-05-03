import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.keysight import KeysightInfiniiVision

@pytest.fixture
def mock_scope():
    with patch('pyvisa.ResourceManager'):
        driver = KeysightInfiniiVision("TCPIP::1.2.3.4::INSTR")
        driver.inst = MagicMock()
        # Ensure *OPC? returns 1 to avoid wait_ready timeouts
        driver.inst.query.return_value = "1"
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
