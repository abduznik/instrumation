import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.fluke_counter import FlukePM6690


@pytest.fixture
def mock_counter():
    with patch('pyvisa.ResourceManager'):
        driver = FlukePM6690("GPIB0::3::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        driver.check_errors_enabled = False
        yield driver


def test_measure_frequency_auto(mock_counter):
    mock_counter.inst.query.return_value = "1000000.0"
    res = mock_counter.measure_frequency()
    assert res.value == 1000000.0
    assert res.unit == "Hz"
    mock_counter.inst.query.assert_any_call(":MEAS:FREQ?")


def test_measure_frequency_with_range(mock_counter):
    mock_counter.inst.query.return_value = "500.0"
    mock_counter.measure_frequency(range="1E6")
    mock_counter.inst.query.assert_any_call(":MEAS:FREQ? 1E6")


def test_measure_period(mock_counter):
    mock_counter.inst.query.return_value = "0.001"
    res = mock_counter.measure_period()
    assert res.value == 0.001
    assert res.unit == "s"
    mock_counter.inst.query.assert_any_call(":MEAS:PER?")


def test_measure_time_interval(mock_counter):
    mock_counter.inst.query.return_value = "0.0005"
    res = mock_counter.measure_time_interval("POS,1", "POS,2")
    assert res.value == 0.0005
    mock_counter.inst.query.assert_any_call(":MEAS:TINT? POS,1,POS,2")


def test_set_impedance(mock_counter):
    mock_counter.set_impedance(50, channel=1)
    mock_counter.inst.write.assert_any_call("INP1:IMP 50")


def test_set_trigger_level(mock_counter):
    mock_counter.set_trigger_level(1.5, channel=2)
    mock_counter.inst.write.assert_any_call("INP2:LEV 1.5")


def test_set_coupling(mock_counter):
    mock_counter.set_coupling("dc", channel=1)
    mock_counter.inst.write.assert_any_call("INP1:COUP DC")


def test_set_auto_range(mock_counter):
    mock_counter.set_auto_range(True, channel=1)
    mock_counter.inst.write.assert_any_call("INP1:RANG:AUTO ON")


def test_default_channel_is_1(mock_counter):
    mock_counter.set_coupling("ac")
    mock_counter.inst.write.assert_any_call("INP1:COUP AC")
