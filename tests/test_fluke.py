import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.fluke import Fluke8846A


@pytest.fixture
def mock_fluke():
    with patch('pyvisa.ResourceManager'):
        driver = Fluke8846A("TCPIP::1.2.3.6::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        # This double doesn't model the SCPI error queue
        driver.check_errors_enabled = False
        yield driver


def test_fluke_measure_dcv(mock_fluke):
    mock_fluke.inst.query.return_value = "5.12345"
    res = mock_fluke.measure_voltage()
    assert res.value == 5.12345
    assert res.unit == "V"
    mock_fluke.inst.query.assert_any_call(":MEAS:VOLT:DC?")


def test_fluke_measure_acv(mock_fluke):
    mock_fluke.inst.query.return_value = "0.98765"
    res = mock_fluke.measure_voltage(ac=True)
    assert res.value == 0.98765
    assert res.unit == "V"
    mock_fluke.inst.query.assert_any_call(":MEAS:VOLT:AC?")


def test_fluke_measure_resistance(mock_fluke):
    mock_fluke.inst.query.return_value = "9998.5"
    res = mock_fluke.measure_resistance()
    assert res.value == 9998.5
    assert res.unit == "Ohm"
    mock_fluke.inst.query.assert_any_call(":MEAS:RES?")


def test_fluke_measure_resistance_4wire(mock_fluke):
    mock_fluke.inst.query.return_value = "9998.5"
    res = mock_fluke.measure_resistance(four_wire=True)
    assert res.value == 9998.5
    assert res.unit == "Ohm"
    mock_fluke.inst.query.assert_any_call(":MEAS:FRES?")


def test_fluke_measure_dci(mock_fluke):
    mock_fluke.inst.query.return_value = "0.05001"
    res = mock_fluke.measure_current()
    assert res.value == 0.05001
    assert res.unit == "A"
    mock_fluke.inst.query.assert_any_call(":MEAS:CURR:DC?")


def test_fluke_measure_aci(mock_fluke):
    mock_fluke.inst.query.return_value = "0.04001"
    res = mock_fluke.measure_current(ac=True)
    assert res.value == 0.04001
    assert res.unit == "A"
    mock_fluke.inst.query.assert_any_call(":MEAS:CURR:AC?")


def test_fluke_measure_frequency(mock_fluke):
    mock_fluke.inst.query.return_value = "1000.0"
    res = mock_fluke.measure_frequency()
    assert res.value == 1000.0
    assert res.unit == "Hz"


def test_fluke_measure_period(mock_fluke):
    mock_fluke.inst.query.return_value = "0.001"
    res = mock_fluke.measure_period()
    assert res.value == 0.001
    assert res.unit == "s"


def test_fluke_measure_temperature(mock_fluke):
    mock_fluke.inst.query.return_value = "23.45"
    res = mock_fluke.measure_temperature()
    assert res.value == 23.45
    assert res.unit == "C"


def test_fluke_measure_capacitance(mock_fluke):
    mock_fluke.inst.query.return_value = "1.0e-6"
    res = mock_fluke.measure_capacitance()
    assert res.value == 1.0e-6
    assert res.unit == "F"


def test_fluke_measure_diode(mock_fluke):
    mock_fluke.inst.query.return_value = "0.6543"
    res = mock_fluke.measure_diode()
    assert res.value == 0.6543
    assert res.unit == "V"


def test_fluke_unsupported_features_return_zero(mock_fluke):
    duty = mock_fluke.measure_duty_cycle()
    assert duty.value == 0.0
    assert duty.unit == "%"

    vpp = mock_fluke.measure_v_peak_to_peak()
    assert vpp.value == 0.0
    assert vpp.unit == "V"


def test_fluke_shutdown_safety_restores_autorange(mock_fluke):
    mock_fluke.shutdown_safety()
    mock_fluke.inst.write.assert_any_call(":VOLT:RANG:AUTO ON")
