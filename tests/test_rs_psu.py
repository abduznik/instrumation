import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.rs_psu import RohdeSchwarzHMP4040


@pytest.fixture
def mock_psu():
    with patch('pyvisa.ResourceManager'):
        driver = RohdeSchwarzHMP4040("TCPIP::10.0.0.5::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "0"
        driver.check_errors_enabled = False
        yield driver


def test_set_voltage_selects_channel(mock_psu):
    mock_psu.set_voltage(5.0, channel=2)
    mock_psu.inst.write.assert_any_call("INST:NSEL 2")
    mock_psu.inst.write.assert_any_call("VOLT 5.0")


def test_set_voltage_default_channel(mock_psu):
    mock_psu.set_voltage(3.3)
    mock_psu.inst.write.assert_any_call("INST:NSEL 1")


def test_get_voltage(mock_psu):
    mock_psu.inst.query.return_value = "12.0"
    assert mock_psu.get_voltage(channel=3) == 12.0
    mock_psu.inst.write.assert_any_call("INST:NSEL 3")
    mock_psu.inst.query.assert_any_call("VOLT?")


def test_set_current_limit(mock_psu):
    mock_psu.set_current_limit(1.0, channel=4)
    mock_psu.inst.write.assert_any_call("INST:NSEL 4")
    mock_psu.inst.write.assert_any_call("CURR 1.0")


def test_get_current(mock_psu):
    mock_psu.inst.query.return_value = "0.75"
    res = mock_psu.get_current(channel=1)
    assert res.value == 0.75
    assert res.unit == "A"


def test_set_output_on_off(mock_psu):
    mock_psu.set_output(True, channel=1)
    mock_psu.inst.write.assert_any_call("OUTP ON")
    mock_psu.set_output(False, channel=2)
    mock_psu.inst.write.assert_any_call("OUTP OFF")


def test_get_output(mock_psu):
    mock_psu.inst.query.return_value = "1"
    assert mock_psu.get_output(channel=1) is True
    mock_psu.inst.query.return_value = "0"
    assert mock_psu.get_output(channel=1) is False


def test_set_ovp(mock_psu):
    mock_psu.set_ovp(30.0, channel=1)
    mock_psu.inst.write.assert_any_call("VOLT:PROT 30.0")


def test_set_ocp(mock_psu):
    mock_psu.set_ocp(2.0, channel=1)
    mock_psu.inst.write.assert_any_call("CURR:PROT 2.0")


def test_clear_protection(mock_psu):
    mock_psu.clear_protection(channel=1)
    mock_psu.inst.write.assert_any_call("FUSE:STAT OFF")


def test_measure_voltage_actual(mock_psu):
    mock_psu.inst.query.return_value = "4.999"
    res = mock_psu.measure_voltage_actual(channel=1)
    assert res.value == 4.999
    assert res.unit == "V"
    mock_psu.inst.query.assert_any_call("MEAS:VOLT?")


def test_measure_current(mock_psu):
    mock_psu.inst.query.return_value = "0.101"
    res = mock_psu.measure_current(channel=2)
    assert res.value == 0.101


def test_set_global_output(mock_psu):
    mock_psu.set_global_output(True)
    mock_psu.inst.write.assert_any_call("OUTP:GEN ON")


def test_shutdown_safety_disables_all_channels(mock_psu):
    mock_psu.shutdown_safety()
    for ch in (1, 2, 3, 4):
        mock_psu.inst.write.assert_any_call("INST:NSEL " + str(ch))
    mock_psu.inst.write.assert_any_call("OUTP:GEN OFF")
