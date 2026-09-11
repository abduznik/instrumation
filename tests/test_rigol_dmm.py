import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.rigol_dmm import RigolDM3068


@pytest.fixture
def mock_dmm():
    with patch('pyvisa.ResourceManager'):
        driver = RigolDM3068("TCPIP::1.2.3.10::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        driver.check_errors_enabled = False
        yield driver


def test_configure_voltage_dc(mock_dmm):
    mock_dmm.configure_voltage_dc()
    mock_dmm.inst.write.assert_any_call(":FUNC:VOLT:DC")


def test_configure_voltage_ac(mock_dmm):
    mock_dmm.configure_voltage_ac()
    mock_dmm.inst.write.assert_any_call(":FUNC:VOLT:AC")


def test_measure_voltage_dc_selects_function_first(mock_dmm):
    mock_dmm.inst.query.return_value = "3.3"
    res = mock_dmm.measure_voltage()
    assert res.value == 3.3
    assert res.unit == "V"
    mock_dmm.inst.write.assert_any_call(":FUNC:VOLT:DC")
    mock_dmm.inst.query.assert_any_call(":MEAS:VOLT:DC?")


def test_measure_voltage_ac(mock_dmm):
    mock_dmm.inst.query.return_value = "1.1"
    res = mock_dmm.measure_voltage(ac=True)
    assert res.value == 1.1
    mock_dmm.inst.write.assert_any_call(":FUNC:VOLT:AC")
    mock_dmm.inst.query.assert_any_call(":MEAS:VOLT:AC?")


def test_measure_resistance_2wire_and_4wire(mock_dmm):
    mock_dmm.inst.query.return_value = "220.0"
    res = mock_dmm.measure_resistance()
    assert res.unit == "Ohm"
    mock_dmm.inst.write.assert_any_call(":FUNC:RES")
    mock_dmm.inst.query.assert_any_call(":MEAS:RES?")

    mock_dmm.measure_resistance(four_wire=True)
    mock_dmm.inst.write.assert_any_call(":FUNC:FRES")
    mock_dmm.inst.query.assert_any_call(":MEAS:FRES?")


def test_measure_current_dc_and_ac(mock_dmm):
    mock_dmm.inst.query.return_value = "0.05"
    res = mock_dmm.measure_current()
    assert res.value == 0.05
    mock_dmm.inst.write.assert_any_call(":FUNC:CURR:DC")
    mock_dmm.inst.query.assert_any_call(":MEAS:CURR:DC?")

    mock_dmm.measure_current(ac=True)
    mock_dmm.inst.write.assert_any_call(":FUNC:CURR:AC")
    mock_dmm.inst.query.assert_any_call(":MEAS:CURR:AC?")


def test_set_auto_range(mock_dmm):
    mock_dmm.set_auto_range(True)
    mock_dmm.inst.write.assert_any_call(":MEAS AUTO")
    mock_dmm.set_auto_range(False)
    mock_dmm.inst.write.assert_any_call(":MEAS MANU")


def test_measure_frequency_and_period(mock_dmm):
    mock_dmm.inst.query.return_value = "500.0"
    res = mock_dmm.measure_frequency()
    assert res.value == 500.0
    assert res.unit == "Hz"
    mock_dmm.inst.write.assert_any_call(":FUNC:FREQ")

    mock_dmm.inst.query.return_value = "0.002"
    res = mock_dmm.measure_period()
    assert res.value == 0.002
    assert res.unit == "s"
    mock_dmm.inst.write.assert_any_call(":FUNC:PER")


def test_measure_capacitance(mock_dmm):
    mock_dmm.inst.query.return_value = "2.2e-6"
    res = mock_dmm.measure_capacitance()
    assert res.value == 2.2e-6
    assert res.unit == "F"
    mock_dmm.inst.write.assert_any_call(":FUNC:CAP")


def test_measure_continuity(mock_dmm):
    mock_dmm.inst.query.return_value = "10.0"
    res = mock_dmm.measure_continuity()
    assert res.value == 10.0
    assert res.unit == "Ohm"


def test_measure_diode(mock_dmm):
    mock_dmm.inst.query.return_value = "0.55"
    res = mock_dmm.measure_diode()
    assert res.value == 0.55
    assert res.unit == "V"


def test_set_digits(mock_dmm):
    mock_dmm.set_digits("7")
    mock_dmm.inst.write.assert_any_call(":MEAS:RES:DIGIT 7")
    mock_dmm.set_digits("INC", four_wire=True)
    mock_dmm.inst.write.assert_any_call(":MEAS:FRES:DIGIT INC")


def test_unsupported_features_return_zero(mock_dmm):
    assert mock_dmm.measure_duty_cycle().value == 0.0
    assert mock_dmm.measure_v_peak_to_peak().value == 0.0


def test_shutdown_safety_selects_voltage_dc(mock_dmm):
    mock_dmm.shutdown_safety()
    mock_dmm.inst.write.assert_any_call(":FUNC:VOLT:DC")
