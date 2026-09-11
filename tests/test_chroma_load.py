import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.chroma_load import Chroma63200A


@pytest.fixture
def mock_load():
    with patch('pyvisa.ResourceManager'):
        driver = Chroma63200A("TCPIP::1.2.3.18::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        driver.check_errors_enabled = False
        yield driver


def test_set_mode_uses_high_range_variant(mock_load):
    mock_load.set_mode("cc")
    mock_load.inst.write.assert_any_call("MODE CCH")
    mock_load.set_mode("CV")
    mock_load.inst.write.assert_any_call("MODE CVH")
    mock_load.set_mode("CR")
    mock_load.inst.write.assert_any_call("MODE CRH")
    mock_load.set_mode("CP")
    mock_load.inst.write.assert_any_call("MODE CPH")


def test_set_mode_invalid_raises(mock_load):
    with pytest.raises(ValueError):
        mock_load.set_mode("BOGUS")


def test_get_mode_maps_range_variant_back(mock_load):
    mock_load.inst.query.return_value = "CCH"
    assert mock_load.get_mode() == "CC"
    mock_load.inst.query.return_value = "CVH"
    assert mock_load.get_mode() == "CV"


def test_get_mode_unknown_variant_passthrough(mock_load):
    mock_load.inst.query.return_value = "BATL"
    assert mock_load.get_mode() == "BATL"


def test_set_get_current(mock_load):
    mock_load.set_current(2.0)
    mock_load.inst.write.assert_any_call("CURR:STAT:L1 2.0")
    mock_load.inst.query.return_value = "2.0"
    assert mock_load.get_current() == 2.0


def test_set_get_voltage(mock_load):
    mock_load.set_voltage(12.0)
    mock_load.inst.write.assert_any_call("VOLT:STAT:L1 12.0")
    mock_load.inst.query.return_value = "12.0"
    assert mock_load.get_voltage() == 12.0


def test_set_get_resistance(mock_load):
    mock_load.set_resistance(50.0)
    mock_load.inst.write.assert_any_call("RES:STAT:L1 50.0")
    mock_load.inst.query.return_value = "50.0"
    assert mock_load.get_resistance() == 50.0


def test_set_get_power(mock_load):
    mock_load.set_power(100.0)
    mock_load.inst.write.assert_any_call("POW:STAT:L1 100.0")
    mock_load.inst.query.return_value = "100.0"
    assert mock_load.get_power() == 100.0


def test_set_input_on_off(mock_load):
    mock_load.set_input(True)
    mock_load.inst.write.assert_any_call("LOAD ON")
    mock_load.set_input(False)
    mock_load.inst.write.assert_any_call("LOAD OFF")


def test_get_input(mock_load):
    mock_load.inst.query.return_value = "1"
    assert mock_load.get_input() is True
    mock_load.inst.query.return_value = "0"
    assert mock_load.get_input() is False


def test_set_short_circuit(mock_load):
    mock_load.set_short_circuit(True)
    mock_load.inst.write.assert_any_call("LOAD:SHOR ON")
    mock_load.set_short_circuit(False)
    mock_load.inst.write.assert_any_call("LOAD:SHOR OFF")


def test_measure_voltage_current_power(mock_load):
    mock_load.inst.query.return_value = "4.999"
    res = mock_load.measure_voltage()
    assert res.value == 4.999
    assert res.unit == "V"

    mock_load.inst.query.return_value = "1.234"
    res = mock_load.measure_current()
    assert res.value == 1.234
    assert res.unit == "A"

    mock_load.inst.query.return_value = "5.5"
    res = mock_load.measure_power()
    assert res.value == 5.5
    assert res.unit == "W"


def test_measure_resistance_unsupported(mock_load):
    res = mock_load.measure_resistance()
    assert res.value == 0.0
    assert res.unit == "Ohm"


def test_protection_methods_unsupported_noop(mock_load):
    mock_load.set_ovp(30.0)
    mock_load.set_ocp(5.0)
    mock_load.set_opp(50.0)


def test_get_protection_status(mock_load):
    mock_load.inst.query.return_value = "OTP,OK"
    assert mock_load.get_protection_status() == "OTP,OK"
    mock_load.inst.query.assert_any_call("LOAD:PROT?")


def test_clear_protection(mock_load):
    mock_load.clear_protection()
    mock_load.inst.write.assert_any_call("LOAD:PROT:CLE")


def test_shutdown_safety(mock_load):
    mock_load.shutdown_safety()
    mock_load.inst.write.assert_any_call("LOAD OFF")
