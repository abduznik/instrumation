import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.siglent_psu import SiglentSPD3303X


@pytest.fixture
def mock_psu():
    with patch('pyvisa.ResourceManager'):
        driver = SiglentSPD3303X("TCPIP::1.2.3.13::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        driver.check_errors_enabled = False
        yield driver


def test_set_voltage_default_channel(mock_psu):
    mock_psu.set_voltage(5.0)
    mock_psu.inst.write.assert_any_call("CH1:VOLT 5.0")


def test_set_voltage_channel_2(mock_psu):
    mock_psu.set_voltage(12.0, channel=2)
    mock_psu.inst.write.assert_any_call("CH2:VOLT 12.0")


def test_get_voltage(mock_psu):
    mock_psu.inst.query.return_value = "3.3"
    val = mock_psu.get_voltage(channel=1)
    assert val == 3.3
    mock_psu.inst.query.assert_any_call("CH1:VOLT?")


def test_set_current_limit(mock_psu):
    mock_psu.set_current_limit(1.0, channel=2)
    mock_psu.inst.write.assert_any_call("CH2:CURR 1.0")


def test_get_current(mock_psu):
    mock_psu.inst.query.return_value = "0.5"
    res = mock_psu.get_current(channel=1)
    assert res.value == 0.5
    assert res.unit == "A"


def test_set_output_on_off(mock_psu):
    mock_psu.set_output(True, channel=1)
    mock_psu.inst.write.assert_any_call("OUTP CH1,ON")
    mock_psu.set_output(False, channel=3)
    mock_psu.inst.write.assert_any_call("OUTP CH3,OFF")


def test_get_output(mock_psu):
    mock_psu.inst.query.return_value = "ON"
    assert mock_psu.get_output(channel=1) is True
    mock_psu.inst.query.return_value = "OFF"
    assert mock_psu.get_output(channel=1) is False


def test_measure_voltage_actual(mock_psu):
    mock_psu.inst.query.return_value = "4.999"
    res = mock_psu.measure_voltage_actual(channel=1)
    assert res.value == 4.999
    assert res.unit == "V"
    mock_psu.inst.query.assert_any_call("MEAS:VOLT? CH1")


def test_measure_current_actual(mock_psu):
    mock_psu.inst.query.return_value = "0.101"
    res = mock_psu.measure_current(channel=2)
    assert res.value == 0.101
    mock_psu.inst.query.assert_any_call("MEAS:CURR? CH2")


def test_measure_power(mock_psu):
    mock_psu.inst.query.return_value = "5.5"
    res = mock_psu.measure_power(channel=1)
    assert res.value == 5.5
    assert res.unit == "W"
    mock_psu.inst.query.assert_any_call("MEAS:POWE? CH1")


def test_set_track_mode(mock_psu):
    mock_psu.set_track_mode(1)
    mock_psu.inst.write.assert_any_call("OUTP:TRACK 1")


def test_set_track_mode_invalid_raises(mock_psu):
    with pytest.raises(ValueError):
        mock_psu.set_track_mode(5)


def test_save_load_state_valid_range(mock_psu):
    mock_psu.save_state(3)
    mock_psu.inst.write.assert_any_call("*SAV 3")
    mock_psu.load_state(5)
    mock_psu.inst.write.assert_any_call("*RCL 5")


def test_save_state_out_of_range_raises(mock_psu):
    with pytest.raises(ValueError):
        mock_psu.save_state(6)
    with pytest.raises(ValueError):
        mock_psu.save_state(0)


def test_ovp_ocp_unsupported(mock_psu):
    mock_psu.set_ovp(30.0)
    mock_psu.set_ocp(2.0)
    mock_psu.clear_protection()


def test_shutdown_safety_disables_all_channels(mock_psu):
    mock_psu.shutdown_safety()
    for ch in (1, 2, 3):
        mock_psu.inst.write.assert_any_call(f"OUTP CH{ch},OFF")
