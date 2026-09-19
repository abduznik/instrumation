import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.keysight_e4990a import KeysightE4990A


@pytest.fixture
def mock_analyzer():
    with patch('pyvisa.ResourceManager'):
        driver = KeysightE4990A("GPIB0::20::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "0"
        driver.check_errors_enabled = False
        yield driver


def test_set_frequency(mock_analyzer):
    mock_analyzer.set_frequency(1e6)
    mock_analyzer.inst.write.assert_any_call("SENS:FREQ:CW 1000000.0")


def test_get_frequency(mock_analyzer):
    mock_analyzer.inst.query.return_value = "1000000.0"
    assert mock_analyzer.get_frequency() == 1e6


def test_set_start_frequency(mock_analyzer):
    mock_analyzer.set_start_frequency(1e6)
    mock_analyzer.inst.write.assert_any_call("SENS:FREQ:STAR 1000000.0")


def test_get_start_frequency(mock_analyzer):
    mock_analyzer.inst.query.return_value = "1000000.0"
    assert mock_analyzer.get_start_frequency() == 1e6


def test_set_stop_frequency(mock_analyzer):
    mock_analyzer.set_stop_frequency(120e6)
    mock_analyzer.inst.write.assert_any_call("SENS:FREQ:STOP 120000000.0")


def test_get_stop_frequency(mock_analyzer):
    mock_analyzer.inst.query.return_value = "120000000.0"
    assert mock_analyzer.get_stop_frequency() == 120e6


def test_set_points(mock_analyzer):
    mock_analyzer.set_points(201)
    mock_analyzer.inst.write.assert_any_call("SENS:SWE:POIN 201")


def test_get_points(mock_analyzer):
    mock_analyzer.inst.query.return_value = "201"
    assert mock_analyzer.get_points() == 201


def test_set_sweep_type(mock_analyzer):
    mock_analyzer.set_sweep_type("log")
    mock_analyzer.inst.write.assert_any_call("SENS:SWE:TYPE LOG")


def test_set_sweep_type_invalid_raises(mock_analyzer):
    with pytest.raises(ValueError):
        mock_analyzer.set_sweep_type("BOGUS")


def test_set_voltage_level(mock_analyzer):
    mock_analyzer.set_voltage_level(0.5)
    mock_analyzer.inst.write.assert_any_call("SOUR:VOLT 0.5")


def test_set_current_level(mock_analyzer):
    mock_analyzer.set_current_level(0.01)
    mock_analyzer.inst.write.assert_any_call("SOUR:CURR 0.01")


def test_set_measurement_function(mock_analyzer):
    mock_analyzer.set_measurement_function("cpd")
    mock_analyzer.inst.write.assert_any_call("CALC:PAR1:DEF CPD")


def test_get_measurement_function(mock_analyzer):
    mock_analyzer.inst.query.return_value = "CPD"
    assert mock_analyzer.get_measurement_function() == "CPD"


def test_set_bias_voltage(mock_analyzer):
    mock_analyzer.set_bias_voltage(2.0)
    mock_analyzer.inst.write.assert_any_call("BIAS:VOLT 2.0")


def test_set_bias_state(mock_analyzer):
    mock_analyzer.set_bias_state(True)
    mock_analyzer.inst.write.assert_any_call("BIAS:STAT ON")


def test_set_trigger_source(mock_analyzer):
    mock_analyzer.set_trigger_source("internal")
    mock_analyzer.inst.write.assert_any_call("TRIG:SOUR INT")


def test_set_trigger_source_invalid_raises(mock_analyzer):
    with pytest.raises(ValueError):
        mock_analyzer.set_trigger_source("BOGUS")


def test_trigger(mock_analyzer):
    mock_analyzer.trigger()
    mock_analyzer.inst.write.assert_any_call("TRIG:IMM")


def test_measure(mock_analyzer):
    mock_analyzer.inst.query.side_effect = ["1.5e-9,0.02", "CPD"]
    res = mock_analyzer.measure()
    assert res.value == (1.5e-9, 0.02)
    assert res.unit == "CPD"


def test_get_trace_data(mock_analyzer):
    mock_analyzer.inst.query.side_effect = ["1.0,0.1,2.0,0.2,3.0,0.3", "CPD"]
    res = mock_analyzer.get_trace_data()
    assert res.value == [(1.0, 0.1), (2.0, 0.2), (3.0, 0.3)]


def test_get_complex_trace(mock_analyzer):
    mock_analyzer.inst.query.return_value = "1.0,2.0,3.0,4.0"
    res = mock_analyzer.get_complex_trace()
    assert res.value == [complex(1.0, 2.0), complex(3.0, 4.0)]
    assert res.unit == "complex"


def test_shutdown_safety(mock_analyzer):
    mock_analyzer.shutdown_safety()
    mock_analyzer.inst.write.assert_any_call("BIAS:STAT OFF")


def test_connect_sets_frequency_limits(mock_analyzer):
    mock_analyzer.connect()
    assert mock_analyzer.min_frequency == 1e6
    assert mock_analyzer.max_frequency == 120e6
