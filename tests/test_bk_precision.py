import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.bk_precision import BKPrecision9130B


@pytest.fixture
def mock_bk():
    with patch('pyvisa.ResourceManager'):
        driver = BKPrecision9130B("TCPIP::1.2.3.7::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        # This double doesn't model the SCPI error queue
        driver.check_errors_enabled = False
        yield driver


def test_set_voltage_selects_channel_first(mock_bk):
    mock_bk.set_voltage(5.0, channel=2)
    mock_bk.inst.write.assert_any_call("INST:NSEL 2")
    mock_bk.inst.write.assert_any_call("VOLT 5.0")


def test_set_voltage_defaults_to_active_channel(mock_bk):
    mock_bk.set_voltage(3.3)
    mock_bk.inst.write.assert_any_call("INST:NSEL 1")
    mock_bk.inst.write.assert_any_call("VOLT 3.3")


def test_get_voltage(mock_bk):
    mock_bk.inst.query.return_value = "12.0"
    val = mock_bk.get_voltage(channel=3)
    assert val == 12.0
    mock_bk.inst.write.assert_any_call("INST:NSEL 3")
    mock_bk.inst.query.assert_any_call("VOLT?")


def test_set_current_limit(mock_bk):
    mock_bk.set_current_limit(1.5, channel=1)
    mock_bk.inst.write.assert_any_call("CURR 1.5")


def test_get_current(mock_bk):
    mock_bk.inst.query.return_value = "0.5"
    res = mock_bk.get_current(channel=2)
    assert res.value == 0.5
    assert res.unit == "A"


def test_set_output_on_off(mock_bk):
    mock_bk.set_output(True, channel=1)
    mock_bk.inst.write.assert_any_call("OUTP ON")
    mock_bk.set_output(False, channel=1)
    mock_bk.inst.write.assert_any_call("OUTP OFF")


def test_get_output(mock_bk):
    mock_bk.inst.query.return_value = "1"
    assert mock_bk.get_output(channel=1) is True
    mock_bk.inst.query.return_value = "0"
    assert mock_bk.get_output(channel=1) is False


def test_measure_voltage_actual(mock_bk):
    mock_bk.inst.query.return_value = "4.999"
    res = mock_bk.measure_voltage_actual(channel=1)
    assert res.value == 4.999
    assert res.unit == "V"
    mock_bk.inst.query.assert_any_call("MEAS:VOLT?")


def test_measure_current(mock_bk):
    mock_bk.inst.query.return_value = "0.101"
    res = mock_bk.measure_current(channel=2)
    assert res.value == 0.101
    assert res.unit == "A"


def test_measure_power(mock_bk):
    mock_bk.inst.query.return_value = "5.5"
    res = mock_bk.measure_power(channel=1)
    assert res.value == 5.5
    assert res.unit == "W"


def test_set_ovp_ocp(mock_bk):
    mock_bk.set_ovp(30.0, channel=1)
    mock_bk.inst.write.assert_any_call("VOLT:PROT 30.0")
    mock_bk.set_ocp(2.0, channel=1)
    mock_bk.inst.write.assert_any_call("CURR:PROT 2.0")


def test_clear_protection(mock_bk):
    mock_bk.clear_protection()
    mock_bk.inst.write.assert_any_call("OUTP:PROT:CLE")


def test_tracking_mode(mock_bk):
    mock_bk.set_tracking_mode(True)
    mock_bk.inst.write.assert_any_call("OUTP:TRAC ON")
    mock_bk.set_tracking_mode(False)
    mock_bk.inst.write.assert_any_call("OUTP:TRAC OFF")


def test_save_load_state_valid_range(mock_bk):
    mock_bk.save_state(5)
    mock_bk.inst.write.assert_any_call("*SAV 5")
    mock_bk.load_state(9)
    mock_bk.inst.write.assert_any_call("*RCL 9")


def test_save_state_out_of_range_raises(mock_bk):
    with pytest.raises(ValueError):
        mock_bk.save_state(10)
    with pytest.raises(ValueError):
        mock_bk.save_state(0)


def test_load_state_out_of_range_raises(mock_bk):
    with pytest.raises(ValueError):
        mock_bk.load_state(10)


def test_shutdown_safety_disables_all_channels(mock_bk):
    mock_bk.shutdown_safety()
    for ch in (1, 2, 3):
        mock_bk.inst.write.assert_any_call(f"INST:NSEL {ch}")
    mock_bk.inst.write.assert_any_call("OUTP OFF")
    mock_bk.inst.write.assert_any_call("VOLT 0.0")


def test_unsupported_signal_measurements_return_zero(mock_bk):
    assert mock_bk.measure_frequency().value == 0.0
    assert mock_bk.measure_duty_cycle().value == 0.0
    assert mock_bk.measure_v_peak_to_peak().value == 0.0
