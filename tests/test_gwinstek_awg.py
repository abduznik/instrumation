import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.gwinstek_awg import GWInstekMFG2000


@pytest.fixture
def mock_awg():
    with patch('pyvisa.ResourceManager'):
        driver = GWInstekMFG2000("TCPIP::1.2.3.24::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        driver.check_errors_enabled = False
        yield driver


def test_set_frequency(mock_awg):
    mock_awg.set_frequency(1000.0)
    mock_awg.inst.write.assert_any_call("SOUR1:FREQ 1000.0")


def test_set_voltage(mock_awg):
    mock_awg.set_voltage(2.0)
    mock_awg.inst.write.assert_any_call("SOUR1:AMP 2.0")


def test_set_amplitude_converts_dbm_to_vpp(mock_awg):
    mock_awg.set_amplitude(10.0)
    mock_awg.inst.write.assert_any_call("SOUR1:AMP 2.0")


def test_set_offset(mock_awg):
    mock_awg.set_offset(0.5)
    mock_awg.inst.write.assert_any_call("SOUR1:DCO 0.5")


def test_set_waveform(mock_awg):
    mock_awg.set_waveform("sin")
    mock_awg.inst.write.assert_any_call("SOUR1:APPL:SIN")
    mock_awg.set_waveform("arb")
    mock_awg.inst.write.assert_any_call("SOUR1:APPL:USER")


def test_set_phase(mock_awg):
    mock_awg.set_phase(30.0)
    mock_awg.inst.write.assert_any_call("SOUR1:PHAS 30.0")


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


def test_set_reference_clock_is_unsupported_no_rosc(mock_awg):
    # The manual defines no ROSC/reference-oscillator command (0 hits in
    # all 361 pages): nothing may be written.
    mock_awg.inst.write.reset_mock()
    mock_awg.set_reference_clock("ext")
    assert mock_awg.inst.write.call_args_list == []


def test_discover_options_no_opt_query(mock_awg):
    # *OPT? is undefined on the MFG-2000 (0 hits for OPT in the manual):
    # querying it would queue -113 "Undefined header".
    mock_awg._discover_options()
    assert mock_awg.options == []
    assert all("*OPT?" not in str(c) for c in mock_awg.inst.query.call_args_list)


def test_start_sweep_time_clamped_to_spec(mock_awg):
    # SWEep:TIME spec is 1 ms ~ 500 s (total sweep time).
    mock_awg.start_sweep(100.0, 1000.0, 10, 100.0)   # 10 * 100 = 1000 s
    mock_awg.inst.write.assert_any_call("SOUR1:SWE:TIME 500.0")
    mock_awg.start_sweep(100.0, 1000.0, 1, 0.0001)   # 0.0001 s
    mock_awg.inst.write.assert_any_call("SOUR1:SWE:TIME 0.001")


def test_shutdown_safety(mock_awg):
    mock_awg.shutdown_safety()
    mock_awg.inst.write.assert_any_call("OUTP1 OFF")
