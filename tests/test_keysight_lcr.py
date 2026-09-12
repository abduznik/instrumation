import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.keysight_lcr import KeysightE4980A


@pytest.fixture
def mock_lcr():
    with patch('pyvisa.ResourceManager'):
        driver = KeysightE4980A("GPIB0::17::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        driver.check_errors_enabled = False
        yield driver


def test_set_get_frequency(mock_lcr):
    mock_lcr.set_frequency(1000.0)
    mock_lcr.inst.write.assert_any_call("FREQ 1000.0")
    mock_lcr.inst.query.return_value = "1000.0"
    assert mock_lcr.get_frequency() == 1000.0


def test_set_voltage_level(mock_lcr):
    mock_lcr.set_voltage_level(1.0)
    mock_lcr.inst.write.assert_any_call("VOLT 1.0")


def test_set_current_level(mock_lcr):
    mock_lcr.set_current_level(0.01)
    mock_lcr.inst.write.assert_any_call("CURR 0.01")


def test_set_get_measurement_function(mock_lcr):
    mock_lcr.set_measurement_function("cpd")
    mock_lcr.inst.write.assert_any_call("FUNC:IMP CPD")
    mock_lcr.inst.query.return_value = "CPD"
    assert mock_lcr.get_measurement_function() == "CPD"


def test_set_auto_range(mock_lcr):
    mock_lcr.set_auto_range(True)
    mock_lcr.inst.write.assert_any_call("FUNC:IMP:RANG:AUTO ON")
    mock_lcr.set_auto_range(False)
    mock_lcr.inst.write.assert_any_call("FUNC:IMP:RANG:AUTO OFF")


def test_set_bias_voltage_and_state(mock_lcr):
    mock_lcr.set_bias_voltage(2.0)
    mock_lcr.inst.write.assert_any_call("BIAS:VOLT 2.0")
    mock_lcr.set_bias_state(True)
    mock_lcr.inst.write.assert_any_call("BIAS:STAT ON")


def test_measure(mock_lcr):
    mock_lcr.inst.query.return_value = "1.234E-9,0.005,0"
    res = mock_lcr.measure()
    assert res.value == (1.234e-9, 0.005)
    mock_lcr.inst.query.assert_any_call("FETC:IMP:FORM?")


def test_trigger(mock_lcr):
    mock_lcr.trigger()
    mock_lcr.inst.write.assert_any_call("TRIG:IMM")


def test_shutdown_safety(mock_lcr):
    mock_lcr.shutdown_safety()
    mock_lcr.inst.write.assert_any_call("BIAS:STAT OFF")
