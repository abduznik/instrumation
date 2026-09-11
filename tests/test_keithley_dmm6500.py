import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.keithley_dmm6500 import KeithleyDMM6500


@pytest.fixture
def mock_dmm():
    with patch('pyvisa.ResourceManager'):
        driver = KeithleyDMM6500("TCPIP::1.2.3.11::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        driver.check_errors_enabled = False
        yield driver


def test_configure_voltage_dc(mock_dmm):
    mock_dmm.configure_voltage_dc()
    mock_dmm.inst.write.assert_any_call('SENS:FUNC "VOLT:DC"')


def test_configure_voltage_ac(mock_dmm):
    mock_dmm.configure_voltage_ac()
    mock_dmm.inst.write.assert_any_call('SENS:FUNC "VOLT:AC"')


def test_measure_voltage_dc(mock_dmm):
    mock_dmm.inst.query.return_value = "5.0"
    res = mock_dmm.measure_voltage()
    assert res.value == 5.0
    assert res.unit == "V"
    mock_dmm.inst.write.assert_any_call('SENS:FUNC "VOLT:DC"')
    mock_dmm.inst.query.assert_any_call("READ?")


def test_measure_voltage_ac(mock_dmm):
    mock_dmm.inst.query.return_value = "1.2"
    res = mock_dmm.measure_voltage(ac=True)
    assert res.value == 1.2
    mock_dmm.inst.write.assert_any_call('SENS:FUNC "VOLT:AC"')


def test_measure_resistance_2wire_and_4wire(mock_dmm):
    mock_dmm.inst.query.return_value = "100.0"
    mock_dmm.measure_resistance()
    mock_dmm.inst.write.assert_any_call('SENS:FUNC "RES"')

    mock_dmm.measure_resistance(four_wire=True)
    mock_dmm.inst.write.assert_any_call('SENS:FUNC "FRES"')


def test_measure_current_dc_and_ac(mock_dmm):
    mock_dmm.inst.query.return_value = "0.01"
    mock_dmm.measure_current()
    mock_dmm.inst.write.assert_any_call('SENS:FUNC "CURR:DC"')

    mock_dmm.measure_current(ac=True)
    mock_dmm.inst.write.assert_any_call('SENS:FUNC "CURR:AC"')


def test_set_auto_range(mock_dmm):
    mock_dmm.set_auto_range(True, func="VOLT:DC")
    mock_dmm.inst.write.assert_any_call("SENS:VOLT:DC:RANG:AUTO ON")
    mock_dmm.set_auto_range(False, func="RES")
    mock_dmm.inst.write.assert_any_call("SENS:RES:RANG:AUTO OFF")


def test_set_nplc(mock_dmm):
    mock_dmm.set_nplc(10, func="VOLT:DC")
    mock_dmm.inst.write.assert_any_call("SENS:VOLT:DC:NPLC 10")


def test_set_offset_compensation(mock_dmm):
    mock_dmm.set_offset_compensation(True)
    mock_dmm.inst.write.assert_any_call("SENS:FRES:OCOM ON")
    mock_dmm.set_offset_compensation(False)
    mock_dmm.inst.write.assert_any_call("SENS:FRES:OCOM OFF")


def test_measure_frequency_and_period(mock_dmm):
    mock_dmm.inst.query.return_value = "1000.0"
    res = mock_dmm.measure_frequency()
    assert res.value == 1000.0
    assert res.unit == "Hz"
    mock_dmm.inst.write.assert_any_call('SENS:FUNC "FREQ"')

    mock_dmm.inst.query.return_value = "0.001"
    res = mock_dmm.measure_period()
    assert res.unit == "s"
    mock_dmm.inst.write.assert_any_call('SENS:FUNC "PER"')


def test_measure_capacitance(mock_dmm):
    mock_dmm.inst.query.return_value = "1e-6"
    res = mock_dmm.measure_capacitance()
    assert res.value == 1e-6
    assert res.unit == "F"
    mock_dmm.inst.write.assert_any_call('SENS:FUNC "CAP"')


def test_measure_continuity(mock_dmm):
    mock_dmm.inst.query.return_value = "20.0"
    res = mock_dmm.measure_continuity()
    assert res.unit == "Ohm"
    mock_dmm.inst.write.assert_any_call('SENS:FUNC "CONT"')


def test_measure_diode(mock_dmm):
    mock_dmm.inst.query.return_value = "0.6"
    res = mock_dmm.measure_diode()
    assert res.unit == "V"
    mock_dmm.inst.write.assert_any_call('SENS:FUNC "DIOD"')


def test_measure_temperature(mock_dmm):
    mock_dmm.inst.query.return_value = "24.1"
    res = mock_dmm.measure_temperature()
    assert res.value == 24.1
    assert res.unit == "C"
    mock_dmm.inst.write.assert_any_call('SENS:FUNC "TEMP"')


def test_unsupported_features_return_zero(mock_dmm):
    assert mock_dmm.measure_duty_cycle().value == 0.0
    assert mock_dmm.measure_v_peak_to_peak().value == 0.0


def test_shutdown_safety_selects_voltage_dc(mock_dmm):
    mock_dmm.shutdown_safety()
    mock_dmm.inst.write.assert_any_call('SENS:FUNC "VOLT:DC"')
