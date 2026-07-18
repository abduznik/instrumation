import pytest
from unittest.mock import MagicMock, patch, call
from instrumation.drivers.rigol import RigolDS1054Z
from instrumation.drivers.base import Oscilloscope
from instrumation.drivers.registry import DriverRegistry


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_scope():
    with patch('pyvisa.ResourceManager'):
        driver = RigolDS1054Z("USB0::0x1AB1::0x04CE::DS1054Z::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "+0,\"No error\""
        driver.connected = True
        yield driver


# ── Connection & Identity ─────────────────────────────────────────────────────

def test_scope_is_oscilloscope():
    assert issubclass(RigolDS1054Z, Oscilloscope)

def test_scope_registration():
    assert "RigolDS1054Z" in [cls.__name__ for cls in DriverRegistry.get_drivers_by_type("SCOPE")]


# ── Basic Control ─────────────────────────────────────────────────────────────

def test_preset(mock_scope):
    mock_scope.inst.query.return_value = "1"
    mock_scope.preset()
    mock_scope.inst.write.assert_any_call("*RST")

def test_run(mock_scope):
    mock_scope.run()
    mock_scope.inst.write.assert_any_call(":RUN")

def test_stop(mock_scope):
    mock_scope.stop()
    mock_scope.inst.write.assert_any_call(":STOP")

def test_single(mock_scope):
    mock_scope.single()
    mock_scope.inst.write.assert_any_call(":SINGle")

def test_force_trigger(mock_scope):
    mock_scope.force_trigger()
    mock_scope.inst.write.assert_any_call(":TFORce")

def test_auto_scale(mock_scope):
    mock_scope.inst.query.return_value = "1"
    mock_scope.auto_scale()
    mock_scope.inst.write.assert_any_call(":AUToscale")


# ── Channel Configuration Round-Trip ──────────────────────────────────────────

def test_channel_display_set_get(mock_scope):
    mock_scope.set_channel_display(1, True)
    mock_scope.inst.write.assert_any_call(":CHANnel1:DISPlay ON")
    mock_scope.inst.query.return_value = "1"
    assert mock_scope.get_channel_display(1) is True

def test_channel_coupling_set_get(mock_scope):
    mock_scope.set_channel_coupling(2, "DC")
    mock_scope.inst.write.assert_any_call(":CHANnel2:COUPling DC")
    mock_scope.inst.query.return_value = "DC"
    assert mock_scope.get_channel_coupling(2) == "DC"

def test_channel_coupling_invalid(mock_scope):
    with pytest.raises(ValueError):
        mock_scope.set_channel_coupling(1, "INVALID")

def test_channel_scale_set_get(mock_scope):
    mock_scope.set_channel_scale(3, 0.5)
    mock_scope.inst.write.assert_any_call(":CHANnel3:SCALe 0.5")
    mock_scope.inst.query.return_value = "0.5"
    assert mock_scope.get_channel_scale(3) == 0.5

def test_channel_offset_set_get(mock_scope):
    mock_scope.set_channel_offset(1, -1.25)
    mock_scope.inst.write.assert_any_call(":CHANnel1:OFFSet -1.25")
    mock_scope.inst.query.return_value = "-1.25"
    assert mock_scope.get_channel_offset(1) == -1.25

def test_channel_probe_set_get(mock_scope):
    mock_scope.set_channel_probe(1, 10.0)
    mock_scope.inst.write.assert_any_call(":CHANnel1:PROBe 10.0")
    mock_scope.inst.query.return_value = "10.0"
    assert mock_scope.get_channel_probe(1) == 10.0

def test_channel_bw_limit_set_get(mock_scope):
    mock_scope.set_channel_bw_limit(1, "20M")
    mock_scope.inst.write.assert_any_call(":CHANnel1:BWLimit 20M")
    mock_scope.inst.query.return_value = "20M"
    assert mock_scope.get_channel_bw_limit(1) == "20M"

def test_channel_bw_limit_invalid(mock_scope):
    with pytest.raises(ValueError):
        mock_scope.set_channel_bw_limit(1, "100M")

def test_channel_invert_set_get(mock_scope):
    mock_scope.set_channel_invert(2, True)
    mock_scope.inst.write.assert_any_call(":CHANnel2:INVert ON")
    mock_scope.inst.query.return_value = "1"
    assert mock_scope.get_channel_invert(2) is True

def test_channel_units_set(mock_scope):
    mock_scope.set_channel_units(1, "VOLTage")
    mock_scope.inst.write.assert_any_call(":CHANnel1:UNITs VOLTAGE")

def test_channel_units_invalid(mock_scope):
    with pytest.raises(ValueError):
        mock_scope.set_channel_units(1, "DECIBEL")

def test_channel_out_of_range(mock_scope):
    with pytest.raises(ValueError):
        mock_scope.set_channel_display(5, True)
    with pytest.raises(ValueError):
        mock_scope.set_channel_scale(0, 1.0)


# ── Timebase ──────────────────────────────────────────────────────────────────

def test_timebase_scale_set_get(mock_scope):
    mock_scope.set_timebase_scale(1e-3)
    mock_scope.inst.write.assert_any_call(":TIMebase:SCALe 0.001")
    mock_scope.inst.query.return_value = "1e-3"
    assert mock_scope.get_timebase_scale() == 1e-3

def test_timebase_offset_set_get(mock_scope):
    mock_scope.set_timebase_offset(0.5)
    mock_scope.inst.write.assert_any_call(":TIMebase:OFFSet 0.5")
    mock_scope.inst.query.return_value = "0.5"
    assert mock_scope.get_timebase_offset() == 0.5

def test_timebase_mode(mock_scope):
    mock_scope.inst.query.return_value = "MAIN"
    assert mock_scope.get_timebase_mode() == "MAIN"


# ── Acquisition ───────────────────────────────────────────────────────────────

def test_acquire_type_set_get(mock_scope):
    mock_scope.set_acquire_type("HRESolution")
    mock_scope.inst.write.assert_any_call(":ACQuire:TYPE HRESolution")
    mock_scope.inst.query.return_value = "HRESolution"
    assert mock_scope.get_acquire_type() == "HRESolution"

def test_acquire_type_invalid(mock_scope):
    with pytest.raises(ValueError):
        mock_scope.set_acquire_type("INVALID")

def test_acquire_averages_set(mock_scope):
    mock_scope.set_acquire_averages(64)
    mock_scope.inst.write.assert_any_call(":ACQuire:AVERages 64")

def test_acquire_averages_invalid_not_power_of_two(mock_scope):
    with pytest.raises(ValueError):
        mock_scope.set_acquire_averages(50)

def test_acquire_averages_invalid_out_of_range(mock_scope):
    with pytest.raises(ValueError):
        mock_scope.set_acquire_averages(2048)

def test_sample_rate(mock_scope):
    mock_scope.inst.query.return_value = "1000000000"
    assert mock_scope.get_sample_rate() == 1e9


# ── Trigger ───────────────────────────────────────────────────────────────────

def test_edge_trigger_source(mock_scope):
    mock_scope.set_edge_trigger_source("CHANnel1")
    mock_scope.inst.write.assert_any_call(":TRIGger:EDGe:SOURce CHANnel1")
    mock_scope.inst.query.return_value = "CHANnel1"
    assert mock_scope.get_edge_trigger_source() == "CHANnel1"

def test_edge_trigger_slope(mock_scope):
    mock_scope.set_edge_trigger_slope("NEGative")
    mock_scope.inst.write.assert_any_call(":TRIGger:EDGe:SLOPe NEGative")
    mock_scope.inst.query.return_value = "NEGative"
    assert mock_scope.get_edge_trigger_slope() == "NEGative"

def test_edge_trigger_slope_invalid(mock_scope):
    with pytest.raises(ValueError):
        mock_scope.set_edge_trigger_slope("INVALID")

def test_edge_trigger_level(mock_scope):
    mock_scope.set_edge_trigger_level(1.5)
    mock_scope.inst.write.assert_any_call(":TRIGger:EDGe:LEVel 1.5")
    mock_scope.inst.query.return_value = "1.5"
    assert mock_scope.get_edge_trigger_level() == 1.5

def test_trigger_sweep(mock_scope):
    mock_scope.set_trigger_sweep("AUTO")
    mock_scope.inst.write.assert_any_call(":TRIGger:SWEep AUTO")
    mock_scope.inst.query.return_value = "AUTO"
    assert mock_scope.get_trigger_sweep() == "AUTO"

def test_trigger_sweep_invalid(mock_scope):
    with pytest.raises(ValueError):
        mock_scope.set_trigger_sweep("INVALID")

def test_trigger_status(mock_scope):
    mock_scope.inst.query.return_value = "TD"
    assert mock_scope.get_trigger_status() == "TD"

def test_set_trigger_convenience(mock_scope):
    mock_scope.set_trigger("CHANnel2", 0.5, "POSITIVE")
    mock_scope.inst.write.assert_any_call(":TRIGger:MODE EDGE")
    mock_scope.inst.write.assert_any_call(":TRIGger:EDGe:SOURce CHANnel2")
    mock_scope.inst.write.assert_any_call(":TRIGger:EDGe:LEVel 0.5")
    mock_scope.inst.write.assert_any_call(":TRIGger:EDGe:SLOPe POSITIVE")


# ── Waveform Readout ──────────────────────────────────────────────────────────

def test_waveform_source(mock_scope):
    mock_scope.set_waveform_source(3)
    mock_scope.inst.write.assert_any_call(":WAVeform:SOURce CHANnel3")
    mock_scope.inst.query.return_value = "CHANnel3"
    assert mock_scope.get_waveform_source() == "CHANnel3"

def test_waveform_mode(mock_scope):
    mock_scope.set_waveform_mode("RAW")
    mock_scope.inst.write.assert_any_call(":WAVeform:MODE RAW")

def test_waveform_mode_invalid(mock_scope):
    with pytest.raises(ValueError):
        mock_scope.set_waveform_mode("INVALID")

def test_waveform_format(mock_scope):
    mock_scope.set_waveform_format("BYTE")
    mock_scope.inst.write.assert_any_call(":WAVeform:FORMat BYTE")

def test_waveform_format_invalid(mock_scope):
    with pytest.raises(ValueError):
        mock_scope.set_waveform_format("FLOAT")


def _make_preamble(x_inc=1e-9, x_origin=0.0, x_ref=0,
                    y_inc=0.01, y_origin=0.5, y_ref=128,
                    points=1000):
    """Helper to build a Rigol preamble response string."""
    return f"0,0,{points},1,{x_inc},{x_origin},{x_ref},{y_inc},{y_origin},{y_ref}"


def test_waveform_preamble_parse(mock_scope):
    mock_scope.inst.query.return_value = _make_preamble()
    pre = mock_scope.get_waveform_preamble()
    assert pre["format"] == 0
    assert pre["type"] == 0
    assert pre["points"] == 1000
    assert pre["count"] == 1
    assert pre["x_increment"] == pytest.approx(1e-9)
    assert pre["x_origin"] == pytest.approx(0.0)
    assert pre["x_reference"] == 0
    assert pre["y_increment"] == pytest.approx(0.01)
    assert pre["y_origin"] == pytest.approx(0.5)
    assert pre["y_reference"] == 128


def test_waveform_preamble_invalid(mock_scope):
    mock_scope.inst.query.return_value = "0,0,1000"
    with pytest.raises(ValueError):
        mock_scope.get_waveform_preamble()


def test_waveform_raw(mock_scope):
    mock_scope.inst.query.return_value = _make_preamble()
    mock_scope.inst.query_binary_values.return_value = [0, 128, 255, 128, 0]
    raw = mock_scope.get_waveform_raw(1)
    mock_scope.inst.write.assert_any_call(":WAVeform:SOURce CHANnel1")
    mock_scope.inst.write.assert_any_call(":WAVeform:FORMat WORD")
    mock_scope.inst.write.assert_any_call(":WAVeform:BYTEorder LSBFirst")
    assert raw == [0, 128, 255, 128, 0]


def test_waveform_get_calibrated(mock_scope):
    """Core test: raw ADC codes are correctly converted to voltage."""
    mock_scope.inst.query.return_value = _make_preamble(
        x_inc=1e-7, x_origin=-5e-4, x_ref=0,
        y_inc=0.01, y_origin=0.0, y_ref=128,
        points=5,
    )
    # Raw codes: 128=0V, 228=1.0V, 28=−1.0V (centered at 128)
    mock_scope.inst.query_binary_values.return_value = [128, 228, 28, 128, 128]
    result = mock_scope.get_waveform(1)

    time_arr, volt_arr = result.value
    assert result.unit == "V"
    assert result.channel == 1

    # Voltage: (128-128)*0.01+0.0 = 0.0
    assert volt_arr[0] == pytest.approx(0.0)
    # Voltage: (228-128)*0.01+0.0 = 1.0
    assert volt_arr[1] == pytest.approx(1.0)
    # Voltage: (28-128)*0.01+0.0 = -1.0
    assert volt_arr[2] == pytest.approx(-1.0)
    # Time axis starts at origin: (0-0)*1e-7 + (-5e-4) = -5e-4
    assert time_arr[0] == pytest.approx(-5e-4)


def test_waveform_x_increment_queries(mock_scope):
    mock_scope.inst.query.return_value = "1e-9"
    assert mock_scope.get_waveform_x_increment() == pytest.approx(1e-9)
    mock_scope.inst.query.return_value = "-0.005"
    assert mock_scope.get_waveform_x_origin() == pytest.approx(-0.005)
    mock_scope.inst.query.return_value = "500"
    assert mock_scope.get_waveform_x_reference() == 500


def test_waveform_y_increment_queries(mock_scope):
    mock_scope.inst.query.return_value = "0.005"
    assert mock_scope.get_waveform_y_increment() == pytest.approx(0.005)
    mock_scope.inst.query.return_value = "0.0"
    assert mock_scope.get_waveform_y_origin() == pytest.approx(0.0)
    mock_scope.inst.query.return_value = "128"
    assert mock_scope.get_waveform_y_reference() == 128


# ── Measurement Helpers ───────────────────────────────────────────────────────

def test_measure_frequency(mock_scope):
    mock_scope.inst.query.return_value = "1.234e6"
    res = mock_scope.measure_frequency(2)
    assert res.value == pytest.approx(1.234e6)
    assert res.unit == "Hz"
    assert res.channel == 2

def test_measure_duty_cycle(mock_scope):
    mock_scope.inst.query.return_value = "50.0"
    res = mock_scope.measure_duty_cycle(1)
    assert res.value == pytest.approx(50.0)
    assert res.unit == "%"

def test_measure_v_peak_to_peak(mock_scope):
    mock_scope.inst.query.return_value = "3.3"
    res = mock_scope.measure_v_peak_to_peak(4)
    assert res.value == pytest.approx(3.3)
    assert res.unit == "V"
    assert res.channel == 4


# ── Context Manager ───────────────────────────────────────────────────────────

def test_context_manager(mock_scope):
    mock_scope.inst.query.return_value = "1"
    with patch.object(mock_scope, 'connect') as mock_connect, \
         patch.object(mock_scope, 'disconnect') as mock_disconnect, \
         patch.object(mock_scope, 'shutdown_safety') as mock_shutdown:
        with mock_scope:
            pass
        mock_connect.assert_called_once()
        mock_shutdown.assert_called_once()
        mock_disconnect.assert_called_once()
