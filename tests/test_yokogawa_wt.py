import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.yokogawa_wt import YokogawaWT310


@pytest.fixture
def mock_meter():
    with patch('pyvisa.ResourceManager'):
        driver = YokogawaWT310("GPIB0::1::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        driver.check_errors_enabled = False
        yield driver


def test_set_output_item(mock_meter):
    mock_meter.set_output_item(1, "u", element=1)
    mock_meter.inst.write.assert_any_call("NUM:ITEM1 U,1")


def test_set_output_preset(mock_meter):
    mock_meter.set_output_preset(2)
    mock_meter.inst.write.assert_any_call("NUM:PRES 2")


def test_set_output_preset_invalid_raises(mock_meter):
    with pytest.raises(ValueError):
        mock_meter.set_output_preset(9)


def test_set_hold(mock_meter):
    mock_meter.set_hold(True)
    mock_meter.inst.write.assert_any_call("NUM:HOLD ON")


def test_read_values(mock_meter):
    mock_meter.inst.query.return_value = "120.5,1.2,144.6"
    res = mock_meter.read_values()
    assert res.value == [120.5, 1.2, 144.6]
    mock_meter.inst.query.assert_any_call("NUM:VAL?")


def test_measure_voltage(mock_meter):
    mock_meter.inst.query.return_value = "120.5"
    res = mock_meter.measure_voltage(element=1)
    assert res.value == 120.5
    assert res.unit == "V"
    mock_meter.inst.write.assert_any_call("NUM:ITEM1 U,1")


def test_measure_current(mock_meter):
    mock_meter.inst.query.return_value = "1.234"
    res = mock_meter.measure_current(element=1)
    assert res.value == 1.234
    assert res.unit == "A"
    mock_meter.inst.write.assert_any_call("NUM:ITEM1 I,1")


def test_measure_active_power(mock_meter):
    mock_meter.inst.query.return_value = "144.6"
    res = mock_meter.measure_active_power(element=1)
    assert res.value == 144.6
    assert res.unit == "W"
    mock_meter.inst.write.assert_any_call("NUM:ITEM1 P,1")


def test_measure_power_factor(mock_meter):
    mock_meter.inst.query.return_value = "0.95"
    res = mock_meter.measure_power_factor(element=1)
    assert res.value == 0.95
    mock_meter.inst.write.assert_any_call("NUM:ITEM1 LAMB,1")


def test_set_update_rate(mock_meter):
    mock_meter.set_update_rate("1s")
    mock_meter.inst.write.assert_any_call("RATE 1S")


def test_zero_calibrate(mock_meter):
    mock_meter.inst.query.return_value = "0"
    assert mock_meter.zero_calibrate() == "0"
    mock_meter.inst.query.assert_any_call("*CAL?")


def test_integration_control(mock_meter):
    mock_meter.start_integration()
    mock_meter.inst.write.assert_any_call("INTEG:STAR")
    mock_meter.stop_integration()
    mock_meter.inst.write.assert_any_call("INTEG:STOP")
    mock_meter.reset_integration()
    mock_meter.inst.write.assert_any_call("INTEG:RES")


def test_unsupported_measures_return_zero(mock_meter):
    assert mock_meter.measure_frequency().value == 0.0
    assert mock_meter.measure_duty_cycle().value == 0.0
    assert mock_meter.measure_v_peak_to_peak().value == 0.0
