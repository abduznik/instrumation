import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.aimtti_psu import AimTTiCPX400DP


@pytest.fixture
def mock_psu():
    with patch('pyvisa.ResourceManager'):
        driver = AimTTiCPX400DP("ASRL3::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "0"
        driver.check_errors_enabled = False
        yield driver


def test_set_voltage_default_channel(mock_psu):
    mock_psu.set_voltage(5.0)
    mock_psu.inst.write.assert_any_call("V1 5.0")


def test_set_voltage_specific_channel(mock_psu):
    mock_psu.set_voltage(12.0, channel=2)
    mock_psu.inst.write.assert_any_call("V2 12.0")


def test_get_voltage(mock_psu):
    mock_psu.inst.query.return_value = "V1 3.300"
    assert mock_psu.get_voltage(channel=1) == 3.3
    mock_psu.inst.query.assert_any_call("V1?")


def test_set_current_limit(mock_psu):
    mock_psu.set_current_limit(1.0, channel=2)
    mock_psu.inst.write.assert_any_call("I2 1.0")


def test_get_current(mock_psu):
    mock_psu.inst.query.return_value = "I1 0.500"
    res = mock_psu.get_current(channel=1)
    assert res.value == 0.5
    assert res.unit == "A"


def test_set_output_on_off(mock_psu):
    mock_psu.set_output(True, channel=1)
    mock_psu.inst.write.assert_any_call("OP1 1")
    mock_psu.set_output(False, channel=2)
    mock_psu.inst.write.assert_any_call("OP2 0")


def test_get_output(mock_psu):
    mock_psu.inst.query.return_value = "1"
    assert mock_psu.get_output(channel=1) is True
    mock_psu.inst.query.return_value = "0"
    assert mock_psu.get_output(channel=1) is False


def test_set_ovp(mock_psu):
    mock_psu.set_ovp(30.0, channel=1)
    mock_psu.inst.write.assert_any_call("OVP1 30.0")


def test_set_ocp(mock_psu):
    mock_psu.set_ocp(2.0, channel=2)
    mock_psu.inst.write.assert_any_call("OCP2 2.0")


def test_clear_protection(mock_psu):
    mock_psu.clear_protection(channel=1)
    mock_psu.inst.write.assert_any_call("TRIPRST")


def test_clear_protection_never_zeroes_trip_points(mock_psu):
    # OVP<n> 0 would set a 0 V trip point, not clear the trip.
    mock_psu.clear_protection(channel=1)
    written = [c.args[0] for c in mock_psu.inst.write.call_args_list]
    assert not [c for c in written if c.startswith(("OVP", "OCP"))]


def test_measure_voltage_actual(mock_psu):
    mock_psu.inst.query.return_value = "4.999V"
    res = mock_psu.measure_voltage_actual(channel=1)
    assert res.value == 4.999
    assert res.unit == "V"
    mock_psu.inst.query.assert_any_call("V1O?")


def test_measure_current(mock_psu):
    mock_psu.inst.query.return_value = "0.101A"
    res = mock_psu.measure_current(channel=2)
    assert res.value == 0.101
    mock_psu.inst.query.assert_any_call("I2O?")


def test_set_track_mode_independent(mock_psu):
    # CONFIG 2 = outputs independent; outputs must be off first (execution error 104).
    mock_psu.set_track_mode(2)
    mock_psu.inst.write.assert_any_call("OP1 0")
    mock_psu.inst.write.assert_any_call("OP2 0")
    mock_psu.inst.write.assert_any_call("CONFIG 2")


def test_set_track_mode_tracking(mock_psu):
    mock_psu.set_track_mode(0)
    mock_psu.inst.write.assert_any_call("CONFIG 0")


def test_set_track_mode_rejects_undefined_modes(mock_psu):
    # 1 (series) and 3 are not CONFIG values on this instrument.
    for mode in (1, 3, 9):
        with pytest.raises(ValueError):
            mock_psu.set_track_mode(mode)


def test_check_errors_uses_eer_not_syst_err(mock_psu):
    mock_psu.check_errors_enabled = True
    mock_psu.identity = {"model": "CPX400DP"}
    mock_psu.inst.query.return_value = "0"
    mock_psu.check_errors()
    mock_psu.inst.query.assert_called_with("EER?")
    assert not mock_psu.error_stack


def test_check_errors_raises_on_execution_error(mock_psu):
    from instrumation.exceptions import ConfigurationError

    mock_psu.check_errors_enabled = True
    mock_psu.identity = {"model": "CPX400DP"}
    mock_psu.inst.query.return_value = "104"
    with pytest.raises(ConfigurationError):
        mock_psu.check_errors()
    assert mock_psu.error_stack == ["104"]


def test_discover_options_sends_no_opt_query(mock_psu):
    mock_psu._discover_options()
    assert mock_psu.options == []
    mock_psu.inst.query.assert_not_called()


def test_shutdown_safety(mock_psu):
    mock_psu.shutdown_safety()
    mock_psu.inst.write.assert_any_call("OP1 0")
    mock_psu.inst.write.assert_any_call("OP2 0")
