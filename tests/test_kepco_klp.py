import pytest
from unittest.mock import MagicMock, patch

from instrumation.drivers.kepco_psu import KepcoKLP
from instrumation.factory import route_idn


@pytest.fixture
def mock_psu():
    with patch('pyvisa.ResourceManager'):
        driver = KepcoKLP("GPIB0::6::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        driver.check_errors_enabled = False
        yield driver


def _writes(driver):
    return [c.args[0] for c in driver.inst.write.call_args_list]


def test_set_voltage(mock_psu):
    mock_psu.set_voltage(32.1)
    assert _writes(mock_psu) == ["VOLT 32.1"]


def test_get_voltage(mock_psu):
    mock_psu.inst.query.return_value = "3.210E1"
    assert mock_psu.get_voltage() == 32.1
    mock_psu.inst.query.assert_any_call("VOLT?")


def test_set_current_limit(mock_psu):
    mock_psu.set_current_limit(4.0)
    assert _writes(mock_psu) == ["CURR 4.0"]


def test_get_current_is_the_programmed_setpoint(mock_psu):
    mock_psu.inst.query.return_value = "4.000E0"
    result = mock_psu.get_current()
    assert result.value == 4.0
    assert result.unit == "A"
    mock_psu.inst.query.assert_any_call("CURR?")


def test_set_output_on_and_off(mock_psu):
    mock_psu.set_output(True)
    mock_psu.set_output(False)
    assert _writes(mock_psu) == ["OUTP ON", "OUTP OFF"]


def test_get_output(mock_psu):
    mock_psu.inst.query.return_value = "1"
    assert mock_psu.get_output() is True
    mock_psu.inst.query.return_value = "0"
    assert mock_psu.get_output() is False


def test_set_ovp_uses_volt_prot(mock_psu):
    mock_psu.set_ovp(40.0)
    assert _writes(mock_psu) == ["VOLT:PROT 40.0"]


def test_set_ocp_uses_curr_prot(mock_psu):
    mock_psu.set_ocp(5.0)
    assert _writes(mock_psu) == ["CURR:PROT 5.0"]


def test_measure_voltage_and_current(mock_psu):
    mock_psu.inst.query.side_effect = lambda cmd: {
        "MEAS:VOLT?": "3.199E1",
        "MEAS:CURR?": "1.02E0",
        "SYST:ERR?": '0,"No error"',
    }[cmd]
    mock_psu.check_errors_enabled = True
    v = mock_psu.measure_voltage_actual()
    i = mock_psu.measure_current()
    assert (v.value, v.unit) == (31.99, "V")
    assert (i.value, i.unit) == (1.02, "A")


def test_get_mode_off_short_circuits(mock_psu):
    mock_psu.inst.query.return_value = "0"
    assert mock_psu.get_mode() == "OFF"
    # FUNC:MODE? must not be queried when the output is disabled.
    mock_psu.inst.query.assert_called_once_with("OUTP?")


def test_get_mode_reads_only_the_actual_field(mock_psu):
    # FUNC:MODE? returns <actual>,<commanded>; the second field is stale.
    mock_psu.inst.query.side_effect = lambda cmd: {
        "OUTP?": "1",
        "FUNC:MODE?": "CURR,VOLT",
        "SYST:ERR?": '0,"No error"',
    }[cmd]
    mock_psu.check_errors_enabled = True
    assert mock_psu.get_mode() == "CC"


def test_sync_config_has_no_wai(mock_psu):
    # The KLP implements no *WAI (Appendix A), so entering with *WAI would
    # post an undefined-command error.
    mock_psu.sync_config()
    assert _writes(mock_psu) == ["*CLS"]
    mock_psu.inst.query.assert_any_call("*OPC?")


def test_discover_options_sends_no_opt_query(mock_psu):
    mock_psu._discover_options()
    assert _writes(mock_psu) == []
    assert mock_psu.options == []


def test_save_and_recall_state(mock_psu):
    mock_psu.save_state(12)
    mock_psu.load_state(40)
    assert _writes(mock_psu) == ["*SAV 12", "*RCL 40"]


def test_state_cell_bounds(mock_psu):
    for bad in (0, 41):
        with pytest.raises(ValueError):
            mock_psu.save_state(bad)


def test_clear_protection_is_not_sent(mock_psu):
    # VOLT:PROT:CLE is mentioned once in prose but is absent from Appendix B.
    assert mock_psu.supports("clear_protection") is False


def test_shutdown_safety_drops_output_then_voltage(mock_psu):
    mock_psu.shutdown_safety()
    assert _writes(mock_psu) == ["OUTP OFF", "VOLT 0.0"]


def test_idn_routing():
    assert route_idn("KEPCO,KLP 75-33-1200,081420191234,V1.01") is KepcoKLP
    assert route_idn("KEPCO,KLP 600-4-1.2K,081420191234,v4.00") is KepcoKLP
