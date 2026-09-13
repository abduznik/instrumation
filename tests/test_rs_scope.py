import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.rs_scope import RohdeSchwarzHMOCompact


@pytest.fixture
def mock_hmo():
    with patch('pyvisa.ResourceManager'):
        driver = RohdeSchwarzHMOCompact("TCPIP::1.2.3.9::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        # This double doesn't model the SCPI error queue
        driver.check_errors_enabled = False
        yield driver


def test_run_stop_single(mock_hmo):
    mock_hmo.run()
    mock_hmo.inst.write.assert_any_call("RUN")
    mock_hmo.stop()
    mock_hmo.inst.write.assert_any_call("STOP")
    mock_hmo.single()
    mock_hmo.inst.write.assert_any_call("SING")


def test_auto_scale(mock_hmo):
    mock_hmo.auto_scale()
    mock_hmo.inst.write.assert_any_call("AUToscale")


def test_channel_display(mock_hmo):
    mock_hmo.set_channel_display(1, True)
    mock_hmo.inst.write.assert_any_call("CHAN1:STAT ON")
    mock_hmo.inst.query.return_value = "1"
    assert mock_hmo.get_channel_display(1) is True


def test_channel_display_scpi_on_off_dialect(mock_hmo):
    # HMO reports CHAN<n>:STAT? as ON/OFF (SCPI boolean), not 1/0.
    # Regression: the getter previously only accepted "1" and therefore
    # always returned False for a genuinely-enabled HMO channel.
    mock_hmo.inst.query.return_value = "ON"
    assert mock_hmo.get_channel_display(1) is True
    mock_hmo.inst.query.return_value = "on"
    assert mock_hmo.get_channel_display(1) is True
    mock_hmo.inst.query.return_value = "OFF"
    assert mock_hmo.get_channel_display(1) is False
    with pytest.raises(ValueError):
        mock_hmo.inst.query.return_value = "BOGUS"
        mock_hmo.get_channel_display(1)


def test_channel_display_invalid_channel_raises(mock_hmo):
    with pytest.raises(ValueError):
        mock_hmo.set_channel_display(5, True)


def test_channel_scale_offset(mock_hmo):
    mock_hmo.set_channel_scale(2, 0.5)
    mock_hmo.inst.write.assert_any_call("CHAN2:SCAL 0.5")
    mock_hmo.inst.query.return_value = "0.5"
    assert mock_hmo.get_channel_scale(2) == 0.5

    mock_hmo.set_channel_offset(2, 1.0)
    mock_hmo.inst.write.assert_any_call("CHAN2:OFFS 1.0")
    mock_hmo.inst.query.return_value = "1.0"
    assert mock_hmo.get_channel_offset(2) == 1.0


def test_channel_coupling(mock_hmo):
    mock_hmo.set_channel_coupling(1, "dc")
    mock_hmo.inst.write.assert_any_call("CHAN1:COUP DC")
    with pytest.raises(ValueError):
        mock_hmo.set_channel_coupling(1, "XX")


def test_timebase_scale_offset(mock_hmo):
    mock_hmo.set_timebase_scale(1e-3)
    mock_hmo.inst.write.assert_any_call("TIM:SCAL 0.001")
    mock_hmo.inst.query.return_value = "0.001"
    assert mock_hmo.get_timebase_scale() == 0.001

    mock_hmo.set_timebase_offset(0.0)
    mock_hmo.inst.write.assert_any_call("TIM:OFFS 0.0")


def test_set_trigger(mock_hmo):
    mock_hmo.set_trigger("CH1", 1.5, "pos")
    mock_hmo.inst.write.assert_any_call("TRIG:A:EDGE:SOUR CH1")
    mock_hmo.inst.write.assert_any_call("TRIG:A:LEV1 1.5")
    mock_hmo.inst.write.assert_any_call("TRIG:A:EDGE:SLOP POS")


def test_set_trigger_invalid_slope_raises(mock_hmo):
    with pytest.raises(ValueError):
        mock_hmo.set_trigger("CH1", 1.5, "XX")


def test_set_trigger_mode(mock_hmo):
    mock_hmo.set_trigger_mode("auto")
    mock_hmo.inst.write.assert_any_call("TRIG:A:MODE AUTO")
    with pytest.raises(ValueError):
        mock_hmo.set_trigger_mode("XX")


def test_get_waveform(mock_hmo):
    mock_hmo.inst.query.return_value = "0.1,0.2,0.3,0.4"
    res = mock_hmo.get_waveform(1)
    assert list(res.value) == pytest.approx([0.1, 0.2, 0.3, 0.4])
    assert res.unit == "V"
    assert res.channel == 1


def test_get_waveform_invalid_channel_raises(mock_hmo):
    with pytest.raises(ValueError):
        mock_hmo.get_waveform(9)


def test_measure_frequency(mock_hmo):
    mock_hmo.inst.query.return_value = "1000.0"
    res = mock_hmo.measure_frequency(1)
    assert res.value == 1000.0
    assert res.unit == "Hz"
    mock_hmo.inst.write.assert_any_call("MEAS1:SOUR CH1")
    mock_hmo.inst.write.assert_any_call("MEAS1:MAIN FREQ")


def test_measure_duty_cycle(mock_hmo):
    mock_hmo.inst.query.return_value = "50.0"
    res = mock_hmo.measure_duty_cycle(1)
    assert res.value == 50.0
    assert res.unit == "%"


def test_measure_v_peak_to_peak(mock_hmo):
    mock_hmo.inst.query.return_value = "2.5"
    res = mock_hmo.measure_v_peak_to_peak(1)
    assert res.value == 2.5
    assert res.unit == "V"


def test_measure_rise_fall_time(mock_hmo):
    mock_hmo.inst.query.return_value = "1e-9"
    res = mock_hmo.measure_rise_time(1)
    assert res.value == 1e-9
    assert res.unit == "s"

    res = mock_hmo.measure_fall_time(1)
    assert res.unit == "s"


def test_measure_period(mock_hmo):
    mock_hmo.inst.query.return_value = "0.001"
    res = mock_hmo.measure_period(1)
    assert res.value == 0.001
    assert res.unit == "s"


def test_get_screenshot(mock_hmo):
    mock_hmo.inst.read_raw.return_value = b"\x89PNGdata"
    data = mock_hmo.get_screenshot()
    assert data == b"\x89PNGdata"
    mock_hmo.inst.write.assert_any_call("HCOP:DATA? PNG")


def test_shutdown_safety(mock_hmo):
    mock_hmo.shutdown_safety()
    mock_hmo.inst.write.assert_any_call("STOP")
