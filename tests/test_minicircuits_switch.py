import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.minicircuits_switch import MiniCircuitsRCSwitch


@pytest.fixture
def mock_switch():
    with patch('pyvisa.ResourceManager'):
        driver = MiniCircuitsRCSwitch("TCPIP::1.2.3.30::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        yield driver


def test_get_id(mock_switch):
    mock_switch.inst.query.return_value = "MN=RC-4SPDT-A18"
    assert mock_switch.get_id() == "RC-4SPDT-A18"
    mock_switch.inst.query.assert_any_call("MN?")


def test_discover_identity_uses_manual_commands(mock_switch):
    responses = {"MN?": "MN=RC-2SPDT-A18", "SN?": "SN=12208010025", "FIRMWARE?": "B3"}
    mock_switch.inst.query.side_effect = lambda cmd: responses[cmd]
    mock_switch._discover_identity()
    assert mock_switch.identity == {
        "manufacturer": "Mini-Circuits",
        "model": "RC-2SPDT-A18",
        "serial": "12208010025",
        "version": "B3",
    }
    queried = [c.args[0] for c in mock_switch.inst.query.call_args_list]
    assert "*IDN?" not in queried
    assert "*OPT?" not in queried


def test_discover_options_no_opt_query(mock_switch):
    mock_switch._discover_options()
    assert mock_switch.options == []
    mock_switch.inst.query.assert_not_called()


def test_set_switch(mock_switch):
    mock_switch.set_switch("a", True)
    mock_switch.inst.write.assert_any_call("SETA=1")
    mock_switch.set_switch("b", False)
    mock_switch.inst.write.assert_any_call("SETB=0")


def test_get_switch(mock_switch):
    mock_switch.inst.query.return_value = "1"   # 0b00000001 -> switch A in state 1
    assert mock_switch.get_switch("a") is True
    assert mock_switch.get_switch("b") is False
    mock_switch.inst.query.return_value = "131"  # 0b10000011 -> A, B, H in state 1
    assert mock_switch.get_switch("a") is True
    assert mock_switch.get_switch("b") is True
    assert mock_switch.get_switch("c") is False
    assert mock_switch.get_switch("h") is True
    mock_switch.inst.query.assert_any_call("SWPORT?")


def test_set_port(mock_switch):
    mock_switch.set_port("a", 4, 3)
    mock_switch.inst.write.assert_any_call("SP4TA:STATE:3")
    mock_switch.set_port("B", 6, 2)
    mock_switch.inst.write.assert_any_call("SP6TB:STATE:2")


def test_get_port(mock_switch):
    mock_switch.inst.query.return_value = "2"
    assert mock_switch.get_port("a", 4) == 2
    mock_switch.inst.query.assert_any_call("SP4TA:STATE?")
    assert mock_switch.get_port("b", 6) == 2
    mock_switch.inst.query.assert_any_call("SP6TB:STATE?")


def test_get_all_switches_bitmask(mock_switch):
    mock_switch.inst.query.return_value = "5"
    assert mock_switch.get_all_switches_bitmask() == 5
    mock_switch.inst.query.assert_any_call("SWPORT?")


def test_get_serial_number(mock_switch):
    mock_switch.inst.query.return_value = "SN=12345"
    assert mock_switch.get_serial_number() == "12345"


def test_get_firmware_version(mock_switch):
    mock_switch.inst.query.return_value = "B3"
    assert mock_switch.get_firmware_version() == "B3"


def test_check_errors_is_noop(mock_switch):
    mock_switch.check_errors()
    mock_switch.inst.query.assert_not_called()


def test_sync_config_is_noop(mock_switch):
    mock_switch.sync_config()
    mock_switch.inst.write.assert_not_called()
    mock_switch.inst.query.assert_not_called()


def test_unsupported_measures_return_zero(mock_switch):
    assert mock_switch.measure_frequency().value == 0.0
    assert mock_switch.measure_duty_cycle().value == 0.0
    assert mock_switch.measure_v_peak_to_peak().value == 0.0
