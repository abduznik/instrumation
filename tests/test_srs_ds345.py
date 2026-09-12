import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.srs_ds345 import SRSDS345


@pytest.fixture
def mock_gen():
    with patch('pyvisa.ResourceManager'):
        driver = SRSDS345("GPIB0::19::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "0"
        driver.check_errors_enabled = False
        yield driver


def test_set_frequency(mock_gen):
    mock_gen.set_frequency(1000.0)
    mock_gen.inst.write.assert_any_call("FREQ 1000.0")


def test_get_frequency(mock_gen):
    mock_gen.inst.query.return_value = "1000.0"
    assert mock_gen.get_frequency() == 1000.0
    mock_gen.inst.query.assert_any_call("FREQ?")


def test_set_amplitude_uses_dbm_suffix(mock_gen):
    mock_gen.set_amplitude(-10.0)
    mock_gen.inst.write.assert_any_call("AMPL -10.0DB")


def test_set_voltage_uses_vpp_suffix(mock_gen):
    mock_gen.set_voltage(2.0)
    mock_gen.inst.write.assert_any_call("AMPL 2.0VP")


def test_set_offset(mock_gen):
    mock_gen.set_offset(0.5)
    mock_gen.inst.write.assert_any_call("OFFS 0.5")


def test_set_waveform_uses_numeric_codes(mock_gen):
    mock_gen.set_waveform("sin")
    mock_gen.inst.write.assert_any_call("FUNC 0")
    mock_gen.set_waveform("SQU")
    mock_gen.inst.write.assert_any_call("FUNC 1")
    mock_gen.set_waveform("ramp")
    mock_gen.inst.write.assert_any_call("FUNC 3")
    mock_gen.set_waveform("noise" if False else "NOIS")
    mock_gen.inst.write.assert_any_call("FUNC 4")


def test_set_waveform_invalid_raises(mock_gen):
    with pytest.raises(ValueError):
        mock_gen.set_waveform("BOGUS")


def test_get_waveform(mock_gen):
    mock_gen.inst.query.return_value = "2"
    assert mock_gen.get_waveform() == "TRI"


def test_set_phase(mock_gen):
    mock_gen.set_phase(90.0)
    mock_gen.inst.write.assert_any_call("PHSE 90.0")


def test_zero_phase(mock_gen):
    mock_gen.zero_phase()
    mock_gen.inst.write.assert_any_call("PCLR")


def test_set_output_is_unsupported_noop(mock_gen):
    mock_gen.set_output(True)


def test_get_output_always_true(mock_gen):
    assert mock_gen.get_output() is True


def test_set_mod_state(mock_gen):
    mock_gen.set_mod_state("AM", True)
    mock_gen.inst.write.assert_any_call("MTYP 1")


def test_start_sweep(mock_gen):
    mock_gen.start_sweep(100.0, 1000.0, 10, 0.1)
    mock_gen.inst.write.assert_any_call("SFRQ 100.0")
    mock_gen.inst.write.assert_any_call("SPAN 900.0")
    mock_gen.inst.write.assert_any_call("SSWP 1")


def test_configure_list_sweep_unsupported(mock_gen):
    mock_gen.configure_list_sweep([1, 2], [3, 4])


def test_set_reference_clock(mock_gen):
    mock_gen.set_reference_clock("external")
    mock_gen.inst.write.assert_any_call("FSRC 1")
    mock_gen.set_reference_clock("internal")
    mock_gen.inst.write.assert_any_call("FSRC 0")


def test_shutdown_safety(mock_gen):
    mock_gen.shutdown_safety()
    mock_gen.inst.write.assert_any_call("AMPL 0.0VP")
