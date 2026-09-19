import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.lakeshore import LakeShore336


@pytest.fixture
def mock_ctrl():
    with patch('pyvisa.ResourceManager'):
        driver = LakeShore336("GPIB0::12::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "0"
        driver.check_errors_enabled = False
        yield driver


def test_get_temperature(mock_ctrl):
    mock_ctrl.inst.query.return_value = "77.350"
    res = mock_ctrl.get_temperature("A")
    assert res.value == 77.350
    assert res.unit == "K"
    assert res.channel == "A"
    mock_ctrl.inst.query.assert_any_call("KRDG? A")


def test_get_temperature_celsius(mock_ctrl):
    mock_ctrl.inst.query.return_value = "23.5"
    res = mock_ctrl.get_temperature_celsius("b")
    assert res.value == 23.5
    assert res.unit == "C"
    mock_ctrl.inst.query.assert_any_call("CRDG? B")


def test_get_sensor_reading(mock_ctrl):
    mock_ctrl.inst.query.return_value = "1082.5"
    res = mock_ctrl.get_sensor_reading("C")
    assert res.value == 1082.5
    mock_ctrl.inst.query.assert_any_call("SRDG? C")


def test_set_setpoint(mock_ctrl):
    mock_ctrl.set_setpoint(1, 77.0)
    mock_ctrl.inst.write.assert_any_call("SETP 1,77.0")


def test_get_setpoint(mock_ctrl):
    mock_ctrl.inst.query.return_value = "77.0"
    assert mock_ctrl.get_setpoint(1) == 77.0
    mock_ctrl.inst.query.assert_any_call("SETP? 1")


def test_set_pid(mock_ctrl):
    mock_ctrl.set_pid(1, 50.0, 20.0, 0.0)
    mock_ctrl.inst.write.assert_any_call("PID 1,50.0,20.0,0.0")


def test_get_pid(mock_ctrl):
    mock_ctrl.inst.query.return_value = "50.0,20.0,0.0"
    assert mock_ctrl.get_pid(1) == (50.0, 20.0, 0.0)


def test_set_heater_range(mock_ctrl):
    mock_ctrl.set_heater_range(1, "high")
    mock_ctrl.inst.write.assert_any_call("RANGE 1,3")


def test_set_heater_range_invalid_raises(mock_ctrl):
    with pytest.raises(ValueError):
        mock_ctrl.set_heater_range(1, "BOGUS")


def test_get_heater_range(mock_ctrl):
    mock_ctrl.inst.query.return_value = "2"
    assert mock_ctrl.get_heater_range(1) == "MEDIUM"


def test_get_heater_output(mock_ctrl):
    mock_ctrl.inst.query.return_value = "42.5"
    res = mock_ctrl.get_heater_output(1)
    assert res.value == 42.5
    assert res.unit == "%"
    mock_ctrl.inst.query.assert_any_call("HTR? 1")


def test_set_ramp_rate(mock_ctrl):
    mock_ctrl.set_ramp_rate(1, 10.0, state=True)
    mock_ctrl.inst.write.assert_any_call("RAMP 1,1,10.0")


def test_get_ramp_rate(mock_ctrl):
    mock_ctrl.inst.query.return_value = "1,10.0"
    enabled, rate = mock_ctrl.get_ramp_rate(1)
    assert enabled is True
    assert rate == 10.0


def test_set_sensor_type(mock_ctrl):
    mock_ctrl.set_sensor_type("A", "1,1,1,0,1")
    mock_ctrl.inst.write.assert_any_call("INTYPE A,1,1,1,0,1")


def test_get_sensor_type(mock_ctrl):
    mock_ctrl.inst.query.return_value = "1,1,1,0,1"
    assert mock_ctrl.get_sensor_type("A") == "1,1,1,0,1"


def test_set_control_mode(mock_ctrl):
    mock_ctrl.set_control_mode(1, "pid")
    mock_ctrl.inst.write.assert_any_call("CMODE 1,1")


def test_set_control_mode_invalid_raises(mock_ctrl):
    with pytest.raises(ValueError):
        mock_ctrl.set_control_mode(1, "BOGUS")


def test_autotune(mock_ctrl):
    mock_ctrl.autotune(1, "PID")
    mock_ctrl.inst.write.assert_any_call("ATUNE 1,2")


def test_autotune_invalid_raises(mock_ctrl):
    with pytest.raises(ValueError):
        mock_ctrl.autotune(1, "BOGUS")


def test_get_alarm_status(mock_ctrl):
    mock_ctrl.inst.query.return_value = "0,0"
    assert mock_ctrl.get_alarm_status("A") == "0,0"


def test_shutdown_safety(mock_ctrl):
    mock_ctrl.shutdown_safety()
    mock_ctrl.inst.write.assert_any_call("RANGE 1,0")
    mock_ctrl.inst.write.assert_any_call("RANGE 2,0")
