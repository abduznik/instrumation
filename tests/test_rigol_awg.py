import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.rigol_awg import RigolDG4000


@pytest.fixture
def mock_awg():
    with patch('pyvisa.ResourceManager'):
        driver = RigolDG4000("TCPIP::1.2.3.23::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        driver.check_errors_enabled = False
        yield driver


def test_set_frequency(mock_awg):
    mock_awg.set_frequency(1000.0)
    mock_awg.inst.write.assert_any_call("SOUR1:FREQ 1000.0")


def test_set_voltage(mock_awg):
    mock_awg.set_voltage(2.0)
    mock_awg.inst.write.assert_any_call("SOUR1:VOLT 2.0")


def test_set_amplitude_converts_dbm_to_vpp(mock_awg):
    mock_awg.set_amplitude(10.0)
    mock_awg.inst.write.assert_any_call("SOUR1:VOLT 2.0")


def test_set_offset(mock_awg):
    mock_awg.set_offset(0.5)
    mock_awg.inst.write.assert_any_call("SOUR1:VOLT:OFFS 0.5")


def test_set_waveform(mock_awg):
    mock_awg.set_waveform("sin")
    mock_awg.inst.write.assert_any_call("SOUR1:APPL:SIN")
    mock_awg.set_waveform("SQU")
    mock_awg.inst.write.assert_any_call("SOUR1:APPL:SQU")


def test_set_phase(mock_awg):
    mock_awg.set_phase(45.0)
    mock_awg.inst.write.assert_any_call("SOUR1:PHAS 45.0")


def test_set_output(mock_awg):
    mock_awg.set_output(True)
    mock_awg.inst.write.assert_any_call("OUTP1 ON")
    mock_awg.set_output(False)
    mock_awg.inst.write.assert_any_call("OUTP1 OFF")


def test_get_output(mock_awg):
    mock_awg.inst.query.return_value = "1"
    assert mock_awg.get_output() is True
    mock_awg.inst.query.return_value = "0"
    assert mock_awg.get_output() is False


def test_set_mod_state(mock_awg):
    mock_awg.set_mod_state("AM", True)
    mock_awg.inst.write.assert_any_call("SOUR1:AM:STAT ON")


def test_start_sweep(mock_awg):
    mock_awg.start_sweep(100.0, 1000.0, 10, 0.1)
    mock_awg.inst.write.assert_any_call("SOUR1:FREQ:STAR 100.0")
    mock_awg.inst.write.assert_any_call("SOUR1:FREQ:STOP 1000.0")
    mock_awg.inst.write.assert_any_call("SOUR1:SWE:TIME 1.0")
    mock_awg.inst.write.assert_any_call("SOUR1:SWE:STAT ON")


def test_configure_list_sweep_unsupported(mock_awg):
    mock_awg.configure_list_sweep([1, 2], [3, 4])


def test_set_reference_clock(mock_awg):
    mock_awg.set_reference_clock("ext")
    mock_awg.inst.write.assert_any_call("SOUR1:ROSC:SOUR EXT")


def test_channel_2_uses_sour2_prefix():
    with patch('pyvisa.ResourceManager'):
        driver = RigolDG4000("TCPIP::1.2.3.23::INSTR", channel=2)
        driver.inst = MagicMock()
        driver.check_errors_enabled = False
        driver.set_frequency(500.0)
        driver.inst.write.assert_any_call("SOUR2:FREQ 500.0")


def test_shutdown_safety(mock_awg):
    mock_awg.shutdown_safety()
    mock_awg.inst.write.assert_any_call("OUTP1 OFF")
