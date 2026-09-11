import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.keysight_psu import KeysightE36313A


@pytest.fixture
def mock_psu():
    with patch('pyvisa.ResourceManager'):
        driver = KeysightE36313A("TCPIP::1.2.3.14::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        driver.check_errors_enabled = False
        yield driver


def test_set_voltage_default_channel(mock_psu):
    mock_psu.set_voltage(5.0)
    mock_psu.inst.write.assert_any_call("VOLT 5.0, (@1)")


def test_set_voltage_specific_channel(mock_psu):
    mock_psu.set_voltage(12.0, channel=2)
    mock_psu.inst.write.assert_any_call("VOLT 12.0, (@2)")


def test_get_voltage(mock_psu):
    mock_psu.inst.query.return_value = "3.3"
    val = mock_psu.get_voltage(channel=1)
    assert val == 3.3
    mock_psu.inst.query.assert_any_call("VOLT? (@1)")


def test_set_current_limit(mock_psu):
    mock_psu.set_current_limit(1.0, channel=3)
    mock_psu.inst.write.assert_any_call("CURR 1.0, (@3)")


def test_get_current(mock_psu):
    mock_psu.inst.query.return_value = "0.5"
    res = mock_psu.get_current(channel=2)
    assert res.value == 0.5
    assert res.unit == "A"


def test_set_output_on_off(mock_psu):
    mock_psu.set_output(True, channel=1)
    mock_psu.inst.write.assert_any_call("OUTP ON, (@1)")
    mock_psu.set_output(False, channel=2)
    mock_psu.inst.write.assert_any_call("OUTP OFF, (@2)")


def test_get_output(mock_psu):
    mock_psu.inst.query.return_value = "1"
    assert mock_psu.get_output(channel=1) is True
    mock_psu.inst.query.return_value = "0"
    assert mock_psu.get_output(channel=1) is False


def test_set_ovp(mock_psu):
    mock_psu.set_ovp(30.0, channel=1)
    mock_psu.inst.write.assert_any_call("VOLT:PROT 30.0, (@1)")


def test_set_ocp_enables_protection_state(mock_psu):
    mock_psu.set_ocp(2.0, channel=1)
    mock_psu.inst.write.assert_any_call("CURR:PROT:STAT ON, (@1)")


def test_clear_protection(mock_psu):
    mock_psu.clear_protection(channel=1)
    mock_psu.inst.write.assert_any_call("VOLT:PROT:CLE (@1)")
    mock_psu.inst.write.assert_any_call("CURR:PROT:CLE (@1)")


def test_measure_voltage_actual(mock_psu):
    mock_psu.inst.query.return_value = "4.999"
    res = mock_psu.measure_voltage_actual(channel=1)
    assert res.value == 4.999
    assert res.unit == "V"
    mock_psu.inst.query.assert_any_call("MEAS:VOLT? (@1)")


def test_measure_current_actual(mock_psu):
    mock_psu.inst.query.return_value = "0.101"
    res = mock_psu.measure_current(channel=2)
    assert res.value == 0.101
    mock_psu.inst.query.assert_any_call("MEAS:CURR? (@2)")


def test_set_output_pairing(mock_psu):
    mock_psu.set_output_pairing("par")
    mock_psu.inst.write.assert_any_call("OUTP:PAIR PAR")


def test_set_output_pairing_invalid_raises(mock_psu):
    with pytest.raises(ValueError):
        mock_psu.set_output_pairing("BOGUS")


def test_shutdown_safety_disables_all_channels(mock_psu):
    mock_psu.shutdown_safety()
    for ch in (1, 2, 3):
        mock_psu.inst.write.assert_any_call(f"OUTP OFF, (@{ch})")
        mock_psu.inst.write.assert_any_call(f"VOLT 0.0, (@{ch})")
