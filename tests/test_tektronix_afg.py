import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.tektronix import TektronixAFG

@pytest.fixture
def mock_afg():
    with patch('pyvisa.ResourceManager') as mock_rm:
        driver = TektronixAFG("TCPIP::1.2.3.4::INSTR")
        driver.inst = MagicMock()
        yield driver

def test_afg_frequency(mock_afg):
    mock_afg.set_frequency(1e6)
    mock_afg.inst.write.assert_any_call("SOURce1:FREQuency:FIXed 1000000.0")

def test_afg_voltage(mock_afg):
    mock_afg.set_voltage(2.5)
    mock_afg.inst.write.assert_any_call("SOURce1:VOLTage:AMPLitude 2.5")

def test_afg_waveform(mock_afg):
    mock_afg.set_waveform("SQU")
    mock_afg.inst.write.assert_any_call("SOURce1:FUNCtion:SHAPe SQUARE")

def test_afg_output(mock_afg):
    mock_afg.set_output(True)
    mock_afg.inst.write.assert_any_call("OUTPut1:STATe ON")

def test_afg_shutdown(mock_afg):
    mock_afg.shutdown_safety()
    mock_afg.inst.write.assert_any_call("OUTPut1:STATe OFF")
