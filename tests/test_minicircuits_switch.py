import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.minicircuits_switch import MiniCircuitsRCSwitch

# Command strings below are taken verbatim from the Mini-Circuits
# "Mechanical Switch Systems" Programming Manual, Rev. B7 (7-Jun-24), section 3.


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


def test_get_serial_number(mock_switch):
    mock_switch.inst.query.return_value = "SN=12208010025"
    assert mock_switch.get_serial_number() == "12208010025"
    mock_switch.inst.query.assert_any_call("SN?")


def test_get_firmware_version(mock_switch):
    mock_switch.inst.query.return_value = "B3"
    assert mock_switch.get_firmware_version() == "B3"
    mock_switch.inst.query.assert_any_call("FIRMWARE?")


def test_discover_identity_uses_mn_sn_firmware_not_idn(mock_switch):
    replies = {"MN?": "MN=RC-2SPDT-A18", "SN?": "SN=12208010025", "FIRMWARE?": "B3"}
    mock_switch.inst.query.side_effect = lambda cmd: replies[cmd]
    mock_switch._discover_identity()
    assert mock_switch.identity["model"] == "RC-2SPDT-A18"
    assert mock_switch.identity["serial"] == "12208010025"
    assert mock_switch.identity["version"] == "B3"
    assert "*IDN?" not in [c.args[0] for c in mock_switch.inst.query.call_args_list]


def test_discover_options_is_empty_and_sends_no_opt_query(mock_switch):
    mock_switch._discover_options()
    assert mock_switch.options == []
    mock_switch.inst.query.assert_not_called()


def test_set_switch(mock_switch):
    mock_switch.set_switch("a", True)
    mock_switch.inst.write.assert_any_call("SETA=1")
    mock_switch.set_switch("b", False)
    mock_switch.inst.write.assert_any_call("SETB=0")


def test_get_switch_reads_swport_bitmask(mock_switch):
    # SWPORT? = 131 = 0b10000011 -> switches A, B and H in state 1.
    mock_switch.inst.query.return_value = "131"
    assert mock_switch.get_switch("a") is True
    assert mock_switch.get_switch("b") is True
    assert mock_switch.get_switch("g") is False
    assert mock_switch.get_switch("h") is True
    mock_switch.inst.query.assert_called_with("SWPORT?")


def test_get_switch_rejects_non_letter(mock_switch):
    with pytest.raises(ValueError):
        mock_switch.get_switch("1")


def test_set_port(mock_switch):
    mock_switch.set_port("a", 4, 3)
    mock_switch.inst.write.assert_any_call("SP4TA:STATE:3")
    mock_switch.set_port("b", 6, 6)
    mock_switch.inst.write.assert_any_call("SP6TB:STATE:6")
    mock_switch.set_port("a", 4, 0)  # 0 = all ports disconnected
    mock_switch.inst.write.assert_any_call("SP4TA:STATE:0")


def test_set_port_rejects_out_of_range(mock_switch):
    with pytest.raises(ValueError):
        mock_switch.set_port("a", 5, 1)
    with pytest.raises(ValueError):
        mock_switch.set_port("a", 4, 5)


def test_get_port(mock_switch):
    mock_switch.inst.query.return_value = "3"
    assert mock_switch.get_port("a", 4) == 3
    mock_switch.inst.query.assert_any_call("SP4TA:STATE?")


def test_get_all_switches_bitmask(mock_switch):
    mock_switch.inst.query.return_value = "131"
    assert mock_switch.get_all_switches_bitmask() == 131
    mock_switch.inst.query.assert_any_call("SWPORT?")


def test_check_errors_is_noop(mock_switch):
    mock_switch.check_errors()
    mock_switch.inst.query.assert_not_called()


def test_unsupported_measures_return_zero(mock_switch):
    assert mock_switch.measure_frequency().value == 0.0
    assert mock_switch.measure_duty_cycle().value == 0.0
    assert mock_switch.measure_v_peak_to_peak().value == 0.0
