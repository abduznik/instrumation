import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.bk_precision_1685b import BKPrecision1685B


@pytest.fixture
def mock_psu():
    with patch('pyvisa.ResourceManager'):
        driver = BKPrecision1685B("ASRL7::INSTR")
        driver.inst = MagicMock()
        # GETS returns <vvv><iii> (x10 each); 6 chars.
        driver._query_value = MagicMock(return_value="050015")
        yield driver


def test_set_voltage_encodes_x10(mock_psu):
    mock_psu.set_voltage(5.0)
    mock_psu.inst.write.assert_any_call("VOLT050")


def test_set_voltage_one_decimal(mock_psu):
    mock_psu.set_voltage(1.0)
    mock_psu.inst.write.assert_any_call("VOLT010")


def test_get_voltage_parses_gets(mock_psu):
    mock_psu._query_value.return_value = "123045"
    assert mock_psu.get_voltage() == 12.3
    mock_psu._query_value.assert_any_call("GETS")


def test_set_current_limit_encodes_x10(mock_psu):
    mock_psu.set_current_limit(2.5)
    mock_psu.inst.write.assert_any_call("CURR025")


def test_get_current_parses_gets(mock_psu):
    mock_psu._query_value.return_value = "050015"
    res = mock_psu.get_current()
    assert res.value == 1.5
    assert res.unit == "A"


def test_set_output_polarity_inverted(mock_psu):
    # Manual: SOUT 0 = ON, 1 = OFF (inverted).
    mock_psu.set_output(True)
    mock_psu.inst.write.assert_any_call("SOUT0")
    mock_psu.set_output(False)
    mock_psu.inst.write.assert_any_call("SOUT1")


def test_get_output_returns_last_state(mock_psu):
    # No output-state readback; get_output mirrors last set_output.
    mock_psu.set_output(True)
    assert mock_psu.get_output() is True
    mock_psu.set_output(False)
    assert mock_psu.get_output() is False


def test_set_ovp_encodes_x10(mock_psu):
    mock_psu.set_ovp(15.1)
    mock_psu.inst.write.assert_any_call("SOVP151")


def test_set_ocp_encodes_x10(mock_psu):
    mock_psu.set_ocp(10.8)
    mock_psu.inst.write.assert_any_call("SOCP108")


def test_clear_protection_unsupported(mock_psu):
    # 1685B has no OVP0/OCP0 clear command; clear_protection is unsupported.
    mock_psu.clear_protection()
    mock_psu.inst.write.assert_not_called()
    assert mock_psu.supports("clear_protection") is False


def test_measure_voltage_actual_parses_getd(mock_psu):
    # GETD returns <vvvv><iiii><s> (V/I x100). 0302 0145 0 -> 3.02 V.
    mock_psu._query_value.return_value = "030201450"
    res = mock_psu.measure_voltage_actual()
    assert res.value == 3.02
    assert res.unit == "V"


def test_measure_current_parses_getd(mock_psu):
    # 0302 0145 0 -> 1.45 A.
    mock_psu._query_value.return_value = "030201450"
    res = mock_psu.measure_current()
    assert res.value == 1.45
    assert res.unit == "A"


def test_preset_zeroes_output(mock_psu):
    mock_psu.preset()
    mock_psu.inst.write.assert_any_call("SOUT1")
    mock_psu.inst.write.assert_any_call("VOLT000")
    mock_psu.inst.write.assert_any_call("CURR000")


def test_check_errors_is_noop(mock_psu):
    mock_psu.check_errors()
    mock_psu.inst.write.assert_not_called()


def test_shutdown_safety(mock_psu):
    mock_psu.shutdown_safety()
    mock_psu.inst.write.assert_any_call("SOUT1")
    mock_psu.inst.write.assert_any_call("VOLT000")


def test_discover_identity_from_gmax(mock_psu):
    # GMAX for 1685B = 60.0V / 5.0A -> "600050".
    mock_psu._query_value.return_value = "600050"
    mock_psu._discover_identity()
    assert mock_psu.identity["model"] == "1685B"
    assert mock_psu.identity["manufacturer"] == "BK Precision"
