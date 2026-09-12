import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.hioki_lcr import HiokiIM3536


@pytest.fixture
def mock_lcr():
    with patch('pyvisa.ResourceManager'):
        driver = HiokiIM3536("GPIB0::18::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        driver.check_errors_enabled = False
        yield driver


def test_set_get_frequency(mock_lcr):
    mock_lcr.set_frequency(1000.0)
    mock_lcr.inst.write.assert_any_call(":FREQ 1000.0")
    mock_lcr.inst.query.return_value = "1000.0"
    assert mock_lcr.get_frequency() == 1000.0


def test_set_voltage_level(mock_lcr):
    mock_lcr.set_voltage_level(1.0)
    mock_lcr.inst.write.assert_any_call(":VOLT:LEV 1.0")


def test_set_get_measurement_function(mock_lcr):
    mock_lcr.set_measurement_function("rx")
    mock_lcr.inst.write.assert_any_call(":FUNC:IMP RX")
    mock_lcr.inst.query.return_value = "RX"
    assert mock_lcr.get_measurement_function() == "RX"


def test_set_auto_range(mock_lcr):
    mock_lcr.set_auto_range(True)
    mock_lcr.inst.write.assert_any_call(":FUNC:IMP:RANG:AUTO ON")


def test_set_bias_voltage_and_state(mock_lcr):
    mock_lcr.set_bias_voltage(2.0)
    mock_lcr.inst.write.assert_any_call(":BIAS:VOLT:LEV 2.0")
    mock_lcr.set_bias_state(True)
    mock_lcr.inst.write.assert_any_call(":BIAS:STAT ON")


def test_measure(mock_lcr):
    mock_lcr.inst.query.return_value = "100.5,0.02"
    res = mock_lcr.measure()
    assert res.value == (100.5, 0.02)
    mock_lcr.inst.query.assert_any_call(":MEAS?")


def test_trigger(mock_lcr):
    mock_lcr.trigger()
    mock_lcr.inst.write.assert_any_call(":TRIG")


def test_shutdown_safety(mock_lcr):
    mock_lcr.shutdown_safety()
    mock_lcr.inst.write.assert_any_call(":BIAS:STAT OFF")
