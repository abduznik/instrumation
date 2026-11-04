import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.uni_t_udp6900 import UniTUDP6900


@pytest.fixture
def mock_psu():
    with patch('pyvisa.ResourceManager'):
        driver = UniTUDP6900("TCPIP::1.2.3.12::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        driver.check_errors_enabled = False
        yield driver


def test_set_voltage_default_channel(mock_psu):
    mock_psu.set_voltage(5.0)
    mock_psu.inst.write.assert_any_call(":SOURce:VOLTage 5.0")


def test_set_voltage_explicit_channel(mock_psu):
    mock_psu.set_voltage(12.0, channel=1)
    mock_psu.inst.write.assert_any_call(":SOURce:VOLTage 12.0")


def test_get_voltage(mock_psu):
    mock_psu.inst.query.return_value = "3.3"
    val = mock_psu.get_voltage(channel=1)
    assert val == 3.3
    mock_psu.inst.query.assert_any_call(":SOURce:VOLTage?")


def test_set_current_limit(mock_psu):
    mock_psu.set_current_limit(1.0, channel=1)
    mock_psu.inst.write.assert_any_call(":SOURce:CURRent 1.0")


def test_get_current(mock_psu):
    mock_psu.inst.query.return_value = "0.5"
    res = mock_psu.get_current(channel=1)
    assert res.value == 0.5
    assert res.unit == "A"
    mock_psu.inst.query.assert_any_call(":SOURce:CURRent?")


def test_set_output_on_off(mock_psu):
    mock_psu.set_output(True, channel=1)
    mock_psu.inst.write.assert_any_call(":OUTPut ON")
    mock_psu.set_output(False)
    mock_psu.inst.write.assert_any_call(":OUTPut OFF")


def test_get_output(mock_psu):
    mock_psu.inst.query.return_value = "ON"
    assert mock_psu.get_output(channel=1) is True
    mock_psu.inst.query.return_value = "OFF"
    assert mock_psu.get_output(channel=1) is False


def test_set_ovp_enables_protection(mock_psu):
    mock_psu.set_ovp(30.0, channel=1)
    mock_psu.inst.write.assert_any_call(":SOURce:VOLTage:PROTection 30.0")
    mock_psu.inst.write.assert_any_call(":SOURce:VOLTage:PROTection:STATe ON")


def test_set_ocp_enables_protection(mock_psu):
    mock_psu.set_ocp(2.0, channel=1)
    mock_psu.inst.write.assert_any_call(":SOURce:CURRent:PROTection 2.0")
    mock_psu.inst.write.assert_any_call(":SOURce:CURRent:PROTection:STATe ON")


def test_clear_protection(mock_psu):
    mock_psu.clear_protection(channel=1)
    mock_psu.inst.write.assert_any_call(":SOURce:VOLTage:PROTection:CLEar")
    mock_psu.inst.write.assert_any_call(":SOURce:CURRent:PROTection:CLEar")


def test_measure_voltage_actual(mock_psu):
    mock_psu.inst.query.return_value = "4.999"
    res = mock_psu.measure_voltage_actual(channel=1)
    assert res.value == 4.999
    assert res.unit == "V"
    mock_psu.inst.query.assert_any_call(":MEASure:VOLTage?")


def test_measure_current_actual(mock_psu):
    mock_psu.inst.query.return_value = "0.101"
    res = mock_psu.measure_current(channel=1)
    assert res.value == 0.101
    assert res.unit == "A"
    mock_psu.inst.query.assert_any_call(":MEASure:CURRent?")


def test_measure_power(mock_psu):
    mock_psu.inst.query.return_value = "5.5"
    res = mock_psu.measure_power(channel=1)
    assert res.value == 5.5
    assert res.unit == "W"
    mock_psu.inst.query.assert_any_call(":MEASure:POWEr?")


def test_save_load_state_valid_range(mock_psu):
    mock_psu.save_state(5)
    mock_psu.inst.write.assert_any_call("*SAV 5")
    mock_psu.load_state(10)
    mock_psu.inst.write.assert_any_call("*RCL 10")


def test_save_state_out_of_range_raises(mock_psu):
    with pytest.raises(ValueError):
        mock_psu.save_state(11)
    with pytest.raises(ValueError):
        mock_psu.save_state(0)


def test_shutdown_safety_disables_output(mock_psu):
    mock_psu.shutdown_safety()
    mock_psu.inst.write.assert_any_call(":OUTPut OFF")
    mock_psu.inst.write.assert_any_call(":SOURce:VOLTage 0.0")
    mock_psu.inst.write.assert_any_call(":SOURce:CURRent 0.0")
