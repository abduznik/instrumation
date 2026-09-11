import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.gwinstek_psu import GWInstekGPP4323


@pytest.fixture
def mock_psu():
    with patch('pyvisa.ResourceManager'):
        driver = GWInstekGPP4323("TCPIP::1.2.3.15::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        driver.check_errors_enabled = False
        yield driver


def test_set_voltage_default_channel(mock_psu):
    mock_psu.set_voltage(5.0)
    mock_psu.inst.write.assert_any_call("SOUR1:VOLT 5.0")


def test_set_voltage_channel_3(mock_psu):
    mock_psu.set_voltage(12.0, channel=3)
    mock_psu.inst.write.assert_any_call("SOUR3:VOLT 12.0")


def test_get_voltage(mock_psu):
    mock_psu.inst.query.return_value = "3.3"
    val = mock_psu.get_voltage(channel=2)
    assert val == 3.3
    mock_psu.inst.query.assert_any_call("SOUR2:VOLT?")


def test_set_current_limit(mock_psu):
    mock_psu.set_current_limit(1.0, channel=4)
    mock_psu.inst.write.assert_any_call("SOUR4:CURR 1.0")


def test_get_current(mock_psu):
    mock_psu.inst.query.return_value = "0.5"
    res = mock_psu.get_current(channel=1)
    assert res.value == 0.5
    assert res.unit == "A"


def test_set_output_on_off(mock_psu):
    mock_psu.set_output(True, channel=1)
    mock_psu.inst.write.assert_any_call("OUTP1:STAT ON")
    mock_psu.set_output(False, channel=2)
    mock_psu.inst.write.assert_any_call("OUTP2:STAT OFF")


def test_get_output(mock_psu):
    mock_psu.inst.query.return_value = "ON"
    assert mock_psu.get_output(channel=1) is True
    mock_psu.inst.query.return_value = "OFF"
    assert mock_psu.get_output(channel=1) is False


def test_set_ovp_enables_protection(mock_psu):
    mock_psu.set_ovp(30.0, channel=2)
    mock_psu.inst.write.assert_any_call("OUTP2:OVP 30.0")
    mock_psu.inst.write.assert_any_call("OUTP2:OVP:STAT ON")


def test_set_ocp_enables_protection(mock_psu):
    mock_psu.set_ocp(2.0, channel=1)
    mock_psu.inst.write.assert_any_call("OUTP1:OCP 2.0")
    mock_psu.inst.write.assert_any_call("OUTP1:OCP:STAT ON")


def test_clear_protection(mock_psu):
    mock_psu.clear_protection(channel=1)
    mock_psu.inst.write.assert_any_call("OUTP1:OVP:STAT OFF")
    mock_psu.inst.write.assert_any_call("OUTP1:OCP:STAT OFF")


def test_measure_voltage_actual(mock_psu):
    mock_psu.inst.query.return_value = "4.999"
    res = mock_psu.measure_voltage_actual(channel=2)
    assert res.value == 4.999
    assert res.unit == "V"
    mock_psu.inst.query.assert_any_call("MEAS2:VOLT?")


def test_measure_current_actual(mock_psu):
    mock_psu.inst.query.return_value = "0.101"
    res = mock_psu.measure_current(channel=3)
    assert res.value == 0.101
    mock_psu.inst.query.assert_any_call("MEAS3:CURR?")


def test_measure_power(mock_psu):
    mock_psu.inst.query.return_value = "5.5"
    res = mock_psu.measure_power(channel=4)
    assert res.value == 5.5
    assert res.unit == "W"
    mock_psu.inst.query.assert_any_call("MEAS4:POW?")


def test_set_series_and_parallel_mode(mock_psu):
    mock_psu.set_series_mode(True)
    mock_psu.inst.write.assert_any_call("OUTP:SER ON")
    mock_psu.set_parallel_mode(True)
    mock_psu.inst.write.assert_any_call("OUTP:PAR ON")


def test_shutdown_safety_disables_all_channels(mock_psu):
    mock_psu.shutdown_safety()
    for ch in (1, 2, 3, 4):
        mock_psu.inst.write.assert_any_call(f"OUTP{ch}:STAT OFF")
        mock_psu.inst.write.assert_any_call(f"SOUR{ch}:VOLT 0.0")
