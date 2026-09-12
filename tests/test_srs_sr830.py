import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.srs_sr830 import SRSSR830


@pytest.fixture
def mock_lockin():
    with patch('pyvisa.ResourceManager'):
        driver = SRSSR830("GPIB0::8::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1000.0"
        driver.check_errors_enabled = False
        yield driver


def test_set_get_reference_frequency(mock_lockin):
    mock_lockin.set_reference_frequency(1000.0)
    mock_lockin.inst.write.assert_any_call("FREQ 1000.0")
    assert mock_lockin.get_reference_frequency() == 1000.0
    mock_lockin.inst.query.assert_any_call("FREQ?")


def test_set_get_reference_phase(mock_lockin):
    mock_lockin.set_reference_phase(45.0)
    mock_lockin.inst.write.assert_any_call("PHAS 45.0")
    mock_lockin.inst.query.return_value = "45.0"
    assert mock_lockin.get_reference_phase() == 45.0


def test_set_sine_output_amplitude(mock_lockin):
    mock_lockin.set_sine_output_amplitude(1.0)
    mock_lockin.inst.write.assert_any_call("SLVL 1.0")


def test_set_harmonic(mock_lockin):
    mock_lockin.set_harmonic(2)
    mock_lockin.inst.write.assert_any_call("HARM 2")


def test_set_sensitivity_rounds_to_nearest_code(mock_lockin):
    mock_lockin.set_sensitivity(10e-6)
    mock_lockin.inst.write.assert_any_call("SENS 11")


def test_set_time_constant_rounds_to_nearest_code(mock_lockin):
    mock_lockin.set_time_constant(1.0)
    mock_lockin.inst.write.assert_any_call("OFLT 10")


def test_measure_xy(mock_lockin):
    mock_lockin.inst.query.return_value = "1.5e-3,0.5e-3"
    res = mock_lockin.measure_xy()
    assert res.value == (1.5e-3, 0.5e-3)
    assert res.unit == "V"
    mock_lockin.inst.query.assert_any_call("SNAP?1,2")


def test_measure_r_theta(mock_lockin):
    mock_lockin.inst.query.return_value = "1.58e-3,18.43"
    res = mock_lockin.measure_r_theta()
    assert res.value == (1.58e-3, 18.43)
    assert res.unit == "V,deg"
    mock_lockin.inst.query.assert_any_call("SNAP?3,4")


def test_auto_gain(mock_lockin):
    mock_lockin.auto_gain()
    mock_lockin.inst.write.assert_any_call("AGAN")


def test_auto_phase(mock_lockin):
    mock_lockin.auto_phase()
    mock_lockin.inst.write.assert_any_call("APHS")


def test_measure_frequency_uses_reference(mock_lockin):
    mock_lockin.inst.query.return_value = "500.0"
    res = mock_lockin.measure_frequency()
    assert res.value == 500.0
    assert res.unit == "Hz"


def test_shutdown_safety(mock_lockin):
    mock_lockin.shutdown_safety()
    mock_lockin.inst.write.assert_any_call("SLVL 0.004")
