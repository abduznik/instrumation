import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.keysight_daq import KeysightDAQ970A


@pytest.fixture
def mock_daq():
    with patch('pyvisa.ResourceManager'):
        driver = KeysightDAQ970A("TCPIP::10.0.0.50::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "0"
        driver.check_errors_enabled = False
        yield driver


def test_format_channel_list_from_list():
    assert KeysightDAQ970A.format_channel_list([101, 102, 203]) == "(@101,102,203)"


def test_format_channel_list_from_range_string():
    assert KeysightDAQ970A.format_channel_list("101:110") == "(@101:110)"


def test_format_channel_list_passthrough():
    assert KeysightDAQ970A.format_channel_list("(@101:110)") == "(@101:110)"


def test_configure_channel_voltage_dc(mock_daq):
    mock_daq.configure_channel([101, 102], "volt:dc")
    mock_daq.inst.write.assert_any_call("CONF:VOLT:DC (@101,102)")


def test_configure_channel_with_range(mock_daq):
    mock_daq.configure_channel([101], "VOLT:DC", range=10, resolution=0.001)
    mock_daq.inst.write.assert_any_call("CONF:VOLT:DC 10,0.001,(@101)")


def test_configure_channel_temperature(mock_daq):
    mock_daq.configure_channel([103], "TEMP", probe_type="TC", sensor="K")
    mock_daq.inst.write.assert_any_call("CONF:TEMP TC,K,(@103)")


def test_configure_channel_invalid_function(mock_daq):
    with pytest.raises(ValueError):
        mock_daq.configure_channel([101], "BOGUS")


def test_configure_channel_fres(mock_daq):
    mock_daq.configure_channel([104], "FRES")
    mock_daq.inst.write.assert_any_call("CONF:FRES (@104)")


def test_measure_scan(mock_daq):
    mock_daq.inst.query.return_value = "1.234,5.678"
    res = mock_daq.measure_scan([101, 102])
    assert res.value == [1.234, 5.678]
    mock_daq.inst.query.assert_any_call("READ? (@101,102)")


def test_read_channel(mock_daq):
    mock_daq.inst.query.return_value = "3.3"
    res = mock_daq.read_channel("101")
    assert res.value == 3.3
    assert res.channel == "101"


def test_set_scan_list(mock_daq):
    mock_daq.set_scan_list([101, 102, 103])
    mock_daq.inst.write.assert_any_call("ROUT:SCAN (@101,102,103)")


def test_start_scan(mock_daq):
    mock_daq.start_scan()
    mock_daq.inst.write.assert_any_call("INIT")


def test_get_scan_data(mock_daq):
    mock_daq.inst.query.return_value = "1.0,2.0,3.0"
    res = mock_daq.get_scan_data()
    assert res.value == [1.0, 2.0, 3.0]
    mock_daq.inst.query.assert_any_call("FETC?")


def test_set_trigger_source(mock_daq):
    mock_daq.set_trigger_source("immediate")
    mock_daq.inst.write.assert_any_call("TRIG:SOUR IMM")


def test_set_trigger_source_invalid_raises(mock_daq):
    with pytest.raises(ValueError):
        mock_daq.set_trigger_source("BOGUS")


def test_close_relay(mock_daq):
    mock_daq.close_relay("203")
    mock_daq.inst.write.assert_any_call("ROUT:CLOS (@203)")


def test_open_relay(mock_daq):
    mock_daq.open_relay([203, 204])
    mock_daq.inst.write.assert_any_call("ROUT:OPEN (@203,204)")


def test_get_relay_state(mock_daq):
    mock_daq.inst.query.return_value = "1"
    assert mock_daq.get_relay_state("203") is True
    mock_daq.inst.query.return_value = "0"
    assert mock_daq.get_relay_state("203") is False


def test_shutdown_safety(mock_daq):
    mock_daq.shutdown_safety()
    mock_daq.inst.write.assert_any_call("ROUT:OPEN (@100:322)")
