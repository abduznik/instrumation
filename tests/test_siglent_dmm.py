import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.siglent_dmm import SiglentSDM3055


@pytest.fixture
def mock_dmm():
    with patch('pyvisa.ResourceManager'):
        driver = SiglentSDM3055("TCPIP::1.2.3.9::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        driver.check_errors_enabled = False
        yield driver


def test_configure_voltage_dc(mock_dmm):
    mock_dmm.configure_voltage_dc()
    mock_dmm.inst.write.assert_any_call("CONF:VOLT:DC")


def test_configure_voltage_ac(mock_dmm):
    mock_dmm.configure_voltage_ac()
    mock_dmm.inst.write.assert_any_call("CONF:VOLT:AC")


def test_measure_voltage_dc(mock_dmm):
    mock_dmm.inst.query.return_value = "3.3"
    res = mock_dmm.measure_voltage()
    assert res.value == 3.3
    assert res.unit == "V"
    mock_dmm.inst.query.assert_any_call("MEAS:VOLT:DC?")


def test_measure_voltage_ac(mock_dmm):
    mock_dmm.inst.query.return_value = "1.5"
    res = mock_dmm.measure_voltage(ac=True)
    assert res.value == 1.5
    mock_dmm.inst.query.assert_any_call("MEAS:VOLT:AC?")


def test_measure_resistance_2wire_and_4wire(mock_dmm):
    mock_dmm.inst.query.return_value = "100.0"
    res = mock_dmm.measure_resistance()
    assert res.unit == "Ohm"
    mock_dmm.inst.query.assert_any_call("MEAS:RES?")

    mock_dmm.measure_resistance(four_wire=True)
    mock_dmm.inst.query.assert_any_call("MEAS:FRES?")


def test_measure_current_dc_and_ac(mock_dmm):
    mock_dmm.inst.query.return_value = "0.02"
    res = mock_dmm.measure_current()
    assert res.value == 0.02
    assert res.unit == "A"
    mock_dmm.inst.query.assert_any_call("MEAS:CURR:DC?")

    mock_dmm.measure_current(ac=True)
    mock_dmm.inst.query.assert_any_call("MEAS:CURR:AC?")


def test_set_auto_range(mock_dmm):
    mock_dmm.set_auto_range(True)
    mock_dmm.inst.write.assert_any_call("VOLT:DC:RANG:AUTO ON")
    mock_dmm.set_auto_range(False)
    mock_dmm.inst.write.assert_any_call("VOLT:DC:RANG:AUTO OFF")


def test_measure_frequency_and_period(mock_dmm):
    mock_dmm.inst.query.return_value = "1000.0"
    res = mock_dmm.measure_frequency()
    assert res.value == 1000.0
    assert res.unit == "Hz"
    mock_dmm.inst.query.assert_any_call("MEAS:FREQ?")

    mock_dmm.inst.query.return_value = "0.001"
    res = mock_dmm.measure_period()
    assert res.value == 0.001
    assert res.unit == "s"


def test_measure_capacitance(mock_dmm):
    mock_dmm.inst.query.return_value = "1e-6"
    res = mock_dmm.measure_capacitance()
    assert res.value == 1e-6
    assert res.unit == "F"


def test_measure_continuity(mock_dmm):
    mock_dmm.inst.query.return_value = "50.0"
    res = mock_dmm.measure_continuity()
    assert res.value == 50.0
    assert res.unit == "Ohm"
    mock_dmm.inst.query.assert_any_call("MEAS:CONT?")


def test_measure_diode(mock_dmm):
    mock_dmm.inst.query.return_value = "0.65"
    res = mock_dmm.measure_diode()
    assert res.value == 0.65
    assert res.unit == "V"


def test_measure_temperature(mock_dmm):
    mock_dmm.inst.query.return_value = "23.4"
    res = mock_dmm.measure_temperature()
    assert res.value == 23.4
    assert res.unit == "C"
    mock_dmm.inst.query.assert_any_call("MEAS:TEMP? RTD,PT100")


def test_set_nplc(mock_dmm):
    mock_dmm.set_nplc(10)
    mock_dmm.inst.write.assert_any_call("VOLT:DC:NPLC 10")
    mock_dmm.set_nplc(1, ac=True)
    mock_dmm.inst.write.assert_any_call("CURR:DC:NPLC 1")


def test_unsupported_features_return_zero(mock_dmm):
    res = mock_dmm.measure_duty_cycle()
    assert res.value == 0.0
    res = mock_dmm.measure_v_peak_to_peak()
    assert res.value == 0.0


def test_shutdown_safety_restores_autorange(mock_dmm):
    mock_dmm.shutdown_safety()
    mock_dmm.inst.write.assert_any_call("VOLT:DC:RANG:AUTO ON")
