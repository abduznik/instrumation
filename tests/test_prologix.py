import pytest
from unittest.mock import MagicMock, patch, call
from instrumation.drivers.prologix import PrologixDriver


@pytest.fixture
def mock_prologix():
    with patch('pyvisa.ResourceManager'):
        driver = PrologixDriver("/dev/cu.usbserial-1410", gpib_address=5)
        driver.inst = MagicMock()
        driver.inst.read.return_value = "response data"
        yield driver


def _connect(driver):
    """Helper: call connect() with the parent's connect patched out."""
    with patch('instrumation.drivers.real.RealDriver.connect'):
        driver.connect()


def test_connect_sets_controller_mode(mock_prologix):
    _connect(mock_prologix)
    mock_prologix.inst.write.assert_any_call("++mode 1")

def test_connect_disables_auto_read(mock_prologix):
    _connect(mock_prologix)
    mock_prologix.inst.write.assert_any_call("++auto 0")

def test_connect_enables_eoi(mock_prologix):
    _connect(mock_prologix)
    mock_prologix.inst.write.assert_any_call("++eoi 1")

def test_connect_sets_gpib_address(mock_prologix):
    _connect(mock_prologix)
    mock_prologix.inst.write.assert_any_call("++addr 5")

def test_set_gpib_address_updates_attribute(mock_prologix):
    mock_prologix.set_gpib_address(12)
    assert mock_prologix.gpib_address == 12

def test_set_gpib_address_sends_command(mock_prologix):
    mock_prologix.set_gpib_address(12)
    # ++addr is a Prologix command — write() does NOT append \n to ++ commands
    mock_prologix.inst.write.assert_any_call("++addr 12")

def test_query_sends_read_eoi(mock_prologix):
    with patch.object(mock_prologix, 'read', return_value="42.0"):
        mock_prologix.query(":MEAS:VOLT:DC?")
    mock_prologix.inst.write.assert_any_call("++read eoi")

def test_query_strips_whitespace(mock_prologix):
    with patch.object(mock_prologix, 'read', return_value="  42.0  "):
        result = mock_prologix.query(":MEAS:VOLT:DC?")
    assert result == "42.0"

def test_write_appends_newline_to_scpi(mock_prologix):
    mock_prologix.write(":FREQ 1GHz")
    mock_prologix.inst.write.assert_called_with(":FREQ 1GHz\n")

def test_write_does_not_double_newline(mock_prologix):
    mock_prologix.write(":FREQ 1GHz\n")
    mock_prologix.inst.write.assert_called_with(":FREQ 1GHz\n")

def test_write_does_not_append_newline_to_prologix_commands(mock_prologix):
    mock_prologix.write("++addr 5")
    mock_prologix.inst.write.assert_called_with("++addr 5")
