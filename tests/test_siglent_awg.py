import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.siglent_awg import SiglentSDG2000X


@pytest.fixture
def mock_awg():
    with patch('pyvisa.ResourceManager'):
        driver = SiglentSDG2000X("TCPIP::1.2.3.22::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "C1:OUTP ON"
        driver.check_errors_enabled = False
        yield driver


def test_set_frequency(mock_awg):
    mock_awg.set_frequency(1000.0)
    mock_awg.inst.write.assert_any_call("C1:BSWV FRQ,1000.0")


def test_set_voltage(mock_awg):
    mock_awg.set_voltage(2.0)
    mock_awg.inst.write.assert_any_call("C1:BSWV AMP,2.0")


def test_set_amplitude_converts_dbm_to_vpp(mock_awg):
    mock_awg.set_amplitude(10.0)
    mock_awg.inst.write.assert_any_call("C1:BSWV AMP,2.0")


def test_set_offset(mock_awg):
    mock_awg.set_offset(0.5)
    mock_awg.inst.write.assert_any_call("C1:BSWV OFST,0.5")


def test_set_waveform(mock_awg):
    mock_awg.set_waveform("sin")
    mock_awg.inst.write.assert_any_call("C1:BSWV WVTP,SINE")
    mock_awg.set_waveform("SQU")
    mock_awg.inst.write.assert_any_call("C1:BSWV WVTP,SQUARE")


def test_set_phase(mock_awg):
    mock_awg.set_phase(90.0)
    mock_awg.inst.write.assert_any_call("C1:BSWV PHSE,90.0")


def test_set_output(mock_awg):
    mock_awg.set_output(True)
    mock_awg.inst.write.assert_any_call("C1:OUTP ON")
    mock_awg.set_output(False)
    mock_awg.inst.write.assert_any_call("C1:OUTP OFF")


def test_get_output(mock_awg):
    mock_awg.inst.query.return_value = "C1:OUTP ON,LOAD,50"
    assert mock_awg.get_output() is True
    mock_awg.inst.query.return_value = "C1:OUTP OFF,LOAD,50"
    assert mock_awg.get_output() is False


def test_set_mod_state(mock_awg):
    mock_awg.set_mod_state("AM", True)
    mock_awg.inst.write.assert_any_call("C1:MDWV STATE,ON")


def test_start_sweep(mock_awg):
    mock_awg.start_sweep(100.0, 1000.0, 10, 0.1)
    mock_awg.inst.write.assert_any_call("C1:SWWV START,100.0")
    mock_awg.inst.write.assert_any_call("C1:SWWV STOP,1000.0")
    mock_awg.inst.write.assert_any_call("C1:SWWV TIME,1.0")
    mock_awg.inst.write.assert_any_call("C1:SWWV STATE,ON")


def test_configure_list_sweep_unsupported(mock_awg):
    mock_awg.configure_list_sweep([1, 2], [3, 4])


def test_set_reference_clock(mock_awg):
    mock_awg.set_reference_clock("ext")
    mock_awg.inst.write.assert_any_call("ROSC EXT")


def test_channel_2_uses_c2_prefix():
    with patch('pyvisa.ResourceManager'):
        driver = SiglentSDG2000X("TCPIP::1.2.3.22::INSTR", channel=2)
        driver.inst = MagicMock()
        driver.check_errors_enabled = False
        driver.set_frequency(500.0)
        driver.inst.write.assert_any_call("C2:BSWV FRQ,500.0")


def test_shutdown_safety(mock_awg):
    mock_awg.shutdown_safety()
    mock_awg.inst.write.assert_any_call("C1:OUTP OFF")
