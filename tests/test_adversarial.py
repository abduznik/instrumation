import os
import pytest
from datetime import datetime
from instrumation.results import MeasurementResult
from instrumation.factory import get_instrument, is_sim_mode, get_rm, _discover_lan_resources
from instrumation.drivers.simulated import (
    SimulatedMultimeter, SimulatedPowerSupply, SimulatedSpectrumAnalyzer,
    SimulatedNetworkAnalyzer, SimulatedOscilloscope, SimulatedSignalGenerator
)
from instrumation.drivers.base import PowerSupply
from instrumation.exceptions import ConfigurationError, OverloadError


_SIM_MODE_LEAKED = "SIM"


def setup_module():
    global _SIM_MODE_LEAKED
    _SIM_MODE_LEAKED = os.environ.get("INSTRUMATION_MODE", "REAL")


def teardown_module():
    os.environ["INSTRUMATION_MODE"] = _SIM_MODE_LEAKED


def _set_sim():
    os.environ["INSTRUMATION_MODE"] = "SIM"


def _set_real():
    os.environ["INSTRUMATION_MODE"] = "REAL"


# ── 1. MeasurementResult edge cases ────────────────────────────────

def test_measurement_len_on_scalar_value():
    r = MeasurementResult(3.14, "V")
    with pytest.raises(TypeError):
        len(r)


def test_measurement_getitem_on_scalar_value():
    r = MeasurementResult(3.14, "V")
    with pytest.raises(TypeError):
        _ = r[0]


def test_measurement_iter_on_scalar_value():
    r = MeasurementResult(3.14, "V")
    with pytest.raises(TypeError):
        iter(r)


def test_measurement_float_on_list_value():
    r = MeasurementResult([1.0, 2.0, 3.0], "V")
    with pytest.raises(TypeError):
        float(r)


def test_measurement_format_on_list_value():
    r = MeasurementResult([1.0, 2.0, 3.0], "V")
    # Should not crash; returns string representation
    result = f"{r:.2f}"
    assert isinstance(result, str)


def test_measurement_float_on_complex_value():
    r = MeasurementResult(1+2j, "V")
    with pytest.raises(TypeError):
        float(r)


def test_measurement_float_on_none_value():
    r = MeasurementResult(None, "V")
    with pytest.raises(TypeError):
        float(r)


def test_measurement_len_on_none_value():
    r = MeasurementResult(None, "V")
    with pytest.raises(TypeError):
        len(r)


def test_measurement_format_on_none_value():
    r = MeasurementResult(None, "V")
    # Should not crash; returns string representation
    result = f"{r:.2f}"
    assert isinstance(result, str)


# ── 2. Simulated PSU state tracking bugs ──────────────────────────

def test_psu_state_tracking_voltage():
    _set_sim()
    psu = get_instrument("PSU_ADDR", "PSU")
    psu.set_voltage(5.0)
    # BUG: get_voltage() returns 0.0 even after set_voltage(5.0)
    volt = psu.get_voltage()
    assert volt == pytest.approx(5.0, abs=1e-6), (
        f"BUG: get_voltage() returned {volt} instead of 5.0. "
        "SimulatedPowerSupply does not track voltage state."
    )


def test_psu_state_tracking_output():
    _set_sim()
    psu = get_instrument("PSU_ADDR", "PSU")
    psu.set_output(True)
    # BUG: get_output() returns False even after set_output(True)
    out = psu.get_output()
    assert out is True, (
        f"BUG: get_output() returned {out} instead of True. "
        "SimulatedPowerSupply does not track output state."
    )


def test_psu_return_type_inconsistency():
    _set_sim()
    psu = get_instrument("PSU_ADDR", "PSU")
    # get_voltage() returns float, but get_current() returns MeasurementResult
    volt = psu.get_voltage()
    curr = psu.get_current()
    assert isinstance(volt, float), (
        f"get_voltage() returned {type(volt).__name__}, expected float"
    )
    assert isinstance(curr, MeasurementResult), (
        f"get_current() returned {type(curr).__name__}, expected MeasurementResult"
    )
    # This inconsistency could break code that treats all get_* uniformly


# ── 3. Safety guardrail validation ─────────────────────────────────

def test_frequency_validation_sim_sg():
    _set_sim()
    sg = get_instrument("SG_ADDR", "SG")
    with pytest.raises(ConfigurationError):
        sg.set_frequency(-1e9)


def test_frequency_validation_above_max():
    _set_sim()
    sg = get_instrument("SG_ADDR", "SG")
    with pytest.raises(ConfigurationError):
        sg.set_frequency(1e15)


def test_power_validation_over_max():
    _set_sim()
    sg = get_instrument("SG_ADDR", "SG")
    with pytest.raises(OverloadError):
        sg.set_amplitude(100.0)


def test_sa_frequency_validation():
    _set_sim()
    sa = get_instrument("SA_ADDR", "SA")
    with pytest.raises(ConfigurationError):
        sa.set_center_freq(-500)


# ── 4. Multiple instrument isolation ──────────────────────────────

def test_instrument_isolation():
    _set_sim()
    dmm1 = get_instrument("DMM1", "DMM")
    dmm2 = get_instrument("DMM2", "DMM")

    # Connect both
    dmm1.connect()
    dmm2.connect()

    # They should be independent objects
    assert dmm1 is not dmm2
    assert dmm1.connected is True
    assert dmm2.connected is True

    dmm1.disconnect()
    assert dmm1.connected is False
    assert dmm2.connected is True  # BUG: if this fails, instruments share state



# ── 5. Factory edge cases ─────────────────────────────────────────

def test_factory_auto_with_no_hardware():
    """AUTO discovery with no hardware should raise ValueError, not hang."""
    from unittest.mock import patch
    _set_real()
    with patch("instrumation.factory.os.path.exists", return_value=False):
        with patch("instrumation.factory._discover_lan_resources", return_value=[]):
            with patch("instrumation.factory._discover_mdns_resources", return_value=[]):
                with patch("instrumation.factory.get_rm") as mock_rm:
                    mock_rm.return_value.list_resources.return_value = []
                    with pytest.raises(ValueError, match="could not find"):
                        get_instrument("AUTO", "DMM")


def test_factory_empty_address():
    _set_sim()
    try:
        instr = get_instrument("", "DMM")
        instr.connect()
        instr.disconnect()
    except Exception as e:
        # Should not crash catastrophically; ideally handled gracefully
        pass


# ── 6. is_sim_mode inconsistency ──────────────────────────────────

def test_is_sim_mode_consistency():
    _set_sim()
    from instrumation.config import is_sim_mode as config_is_sim
    assert is_sim_mode() is True
    assert config_is_sim() is True

    _SIMULATED = "SIMULATED"
    _REAL = "REAL"

    os.environ["INSTRUMATION_MODE"] = _SIMULATED
    # BUG: factory.py is_sim_mode() does NOT recognize "SIMULATED"
    assert is_sim_mode() is True, (
        "BUG: factory.is_sim_mode() returned False for 'SIMULATED'. "
        "config.is_sim_mode() supports both 'SIM' and 'SIMULATED'."
    )
    assert config_is_sim() is True

    os.environ["INSTRUMATION_MODE"] = _REAL
    assert is_sim_mode() is False
    assert config_is_sim() is False


# ── 7. Async method on non-existent method ────────────────────────

def test_async_nonexistent_method():
    _set_sim()
    dmm = get_instrument("DMM_ADDR", "DMM")
    with pytest.raises(AttributeError):
        # async_nonexistent should not silently create an invalid wrapper
        _ = dmm.async_nonexistent_method


# ── 8. SignalGenerator min_frequency guard ────────────────────────

def test_sg_min_frequency_protection():
    _set_sim()
    sg = get_instrument("SG_ADDR", "SG")
    sg.max_power_dbm = 25.0
    with pytest.raises(ConfigurationError):
        sg.set_frequency(-100)


# ── 9. MeasurementResult with complex to_dict round-trip ──────────

def test_measurement_complex_to_dict():
    r = MeasurementResult(1+2j, "V")
    d = r.to_dict()
    assert d["value"] == {"real": 1.0, "imag": 2.0}, f"Got {d['value']}"

    # Round-trip through JSON
    import json
    s = r.to_json()
    loaded = json.loads(s)
    assert loaded["value"] == {"real": 1.0, "imag": 2.0}


# ── 10. Station double-connect protection ─────────────────────────

def test_station_double_connect():
    from instrumation.station import Station
    from unittest.mock import patch, MagicMock

    with patch('os.path.exists', return_value=True):
        with patch('toml.load') as mock_load:
            mock_load.return_value = {
                "instruments": {
                    "sa": {"driver": "SA", "address": "TCPIP::1::INSTR"}
                }
            }
            with patch('instrumation.station.get_instrument') as mock_get:
                mock_inst = MagicMock()
                mock_get.return_value = mock_inst

                station = Station("dummy.toml")
                # Connect once
                station.connect()
                # Connect again (double connect)
                station.connect()
                # Should not crash, and connect should be called twice
                assert mock_inst.connect.call_count == 2


# ── 11. SimulatedOscilloscope screenshot type ─────────────────────

def test_oscilloscope_screenshot_type():
    _set_sim()
    scope = get_instrument("SCOPE_ADDR", "SCOPE")
    screenshot = scope.get_screenshot()
    assert isinstance(screenshot, bytes), (
        f"get_screenshot() returned {type(screenshot).__name__}, expected bytes"
    )


# ── 12. Repeated connect/disconnect cycling ───────────────────────

def test_repeated_connect_cycle():
    _set_sim()
    dmm = get_instrument("DMM_CYCLE", "DMM")
    for i in range(10):
        dmm.connect()
        assert dmm.connected is True
        _ = dmm.measure_voltage()
        dmm.disconnect()
        assert dmm.connected is False


# ── 13. MeasurementResult timestamp consistency ───────────────────

def test_measurement_timestamp_different_instances():
    r1 = MeasurementResult(1.0, "V")
    r2 = MeasurementResult(2.0, "V")
    # Timestamps should be different (or at least this shouldn't crash)
    assert r1.timestamp <= r2.timestamp
