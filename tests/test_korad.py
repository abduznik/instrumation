import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.korad import KoradKA3005P


@pytest.fixture
def mock_psu():
    with patch('pyvisa.ResourceManager'):
        driver = KoradKA3005P("ASRL5::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "12.00"
        yield driver


def test_get_id(mock_psu):
    mock_psu.inst.query.return_value = "KORADKA3005PV2.0"
    assert mock_psu.get_id() == "KORADKA3005PV2.0"
    mock_psu.inst.query.assert_any_call("*IDN?")


def test_set_voltage_formats_two_decimals(mock_psu):
    mock_psu.set_voltage(5.0)
    mock_psu.inst.write.assert_any_call("VSET1:5.00")


def test_get_voltage(mock_psu):
    mock_psu.inst.query.return_value = "12.34"
    assert mock_psu.get_voltage() == 12.34
    mock_psu.inst.query.assert_any_call("VSET1?")


def test_set_current_limit_formats_three_decimals(mock_psu):
    mock_psu.set_current_limit(1.5)
    mock_psu.inst.write.assert_any_call("ISET1:1.500")


def test_get_current(mock_psu):
    mock_psu.inst.query.return_value = "0.125"
    res = mock_psu.get_current()
    assert res.value == 0.125
    assert res.unit == "A"
    mock_psu.inst.query.assert_any_call("ISET1?")


def test_set_output_on_off(mock_psu):
    mock_psu.set_output(True)
    mock_psu.inst.write.assert_any_call("OUT1")
    mock_psu.set_output(False)
    mock_psu.inst.write.assert_any_call("OUT0")


def test_get_output_true_when_bit6_set(mock_psu):
    mock_psu.inst.query.return_value = chr(0x40)
    assert mock_psu.get_output() is True


def test_get_output_false_when_bit6_clear(mock_psu):
    mock_psu.inst.query.return_value = chr(0x00)
    assert mock_psu.get_output() is False


def test_get_output_empty_status_is_false(mock_psu):
    mock_psu.inst.query.return_value = ""
    assert mock_psu.get_output() is False


def test_set_ovp_sets_voltage_and_enables(mock_psu):
    mock_psu.set_ovp(30.0)
    mock_psu.inst.write.assert_any_call("VSET1:30.00")
    mock_psu.inst.write.assert_any_call("OVP1")


def test_set_ocp_sets_current_and_enables(mock_psu):
    mock_psu.set_ocp(2.0)
    mock_psu.inst.write.assert_any_call("ISET1:2.000")
    mock_psu.inst.write.assert_any_call("OCP1")


def test_clear_protection(mock_psu):
    mock_psu.clear_protection()
    mock_psu.inst.write.assert_any_call("OVP0")
    mock_psu.inst.write.assert_any_call("OCP0")


def test_measure_voltage_actual(mock_psu):
    mock_psu.inst.query.return_value = "4.999"
    res = mock_psu.measure_voltage_actual()
    assert res.value == 4.999
    assert res.unit == "V"
    mock_psu.inst.query.assert_any_call("VOUT1?")


def test_measure_current(mock_psu):
    mock_psu.inst.query.return_value = "0.101"
    res = mock_psu.measure_current()
    assert res.value == 0.101
    mock_psu.inst.query.assert_any_call("IOUT1?")


def test_set_track_mode(mock_psu):
    mock_psu.set_track_mode(1)
    mock_psu.inst.write.assert_any_call("TRACK1")


def test_set_track_mode_invalid_raises(mock_psu):
    with pytest.raises(ValueError):
        mock_psu.set_track_mode(9)


def test_save_load_state(mock_psu):
    mock_psu.save_state(3)
    mock_psu.inst.write.assert_any_call("SAV3")
    mock_psu.load_state(5)
    mock_psu.inst.write.assert_any_call("RCL5")


def test_save_state_out_of_range_raises(mock_psu):
    with pytest.raises(ValueError):
        mock_psu.save_state(6)
    with pytest.raises(ValueError):
        mock_psu.save_state(0)


def test_preset_zeroes_output(mock_psu):
    mock_psu.preset()
    mock_psu.inst.write.assert_any_call("OUT0")
    mock_psu.inst.write.assert_any_call("VSET1:0.00")
    mock_psu.inst.write.assert_any_call("ISET1:0.000")


def test_check_errors_is_noop(mock_psu):
    mock_psu.check_errors()
    mock_psu.inst.query.assert_not_called()


def test_shutdown_safety(mock_psu):
    mock_psu.shutdown_safety()
    mock_psu.inst.write.assert_any_call("OUT0")
    mock_psu.inst.write.assert_any_call("VSET1:0.00")
