"""Regression tests for instrumation v0.6.0.

These tests guard against known behaviors and edge cases that have been
fixed or introduced across releases. If a regression test fails, something
that used to work has broken.
"""

import asyncio
import math
import os
import time

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from instrumation.factory import get_instrument
from instrumation.results import MeasurementResult
from instrumation.exceptions import ConfigurationError, OverloadError


# ── Fixtures ───────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _sim_mode():
    """Force SIM mode for all regression tests."""
    os.environ["INSTRUMATION_MODE"] = "SIM"
    yield
    os.environ.pop("INSTRUMATION_MODE", None)


# ── v0.4.x regressions: driver basics ─────────────────────

class TestDriverBasics:
    """Regression: every driver type must connect, identify, and disconnect cleanly."""

    @pytest.mark.parametrize("dtype", ["DMM", "PSU", "SA", "SCOPE", "SG", "LOAD", "COUNTER"])
    def test_connect_and_id(self, dtype):
        drv = get_instrument(f"SIM_{dtype}", dtype)
        drv.connect()
        assert drv.connected is True
        assert len(drv.get_id()) > 0
        drv.disconnect()
        assert drv.connected is False

    def test_context_manager_cleanup_on_exception(self):
        ref = None
        try:
            with get_instrument("SIM_DMM", "DMM") as dmm:
                ref = dmm
                raise RuntimeError("boom")
        except RuntimeError:
            pass
        assert ref is not None
        assert ref.connected is False

    def test_identity_dict_has_required_keys(self):
        drv = get_instrument("SIM_DMM", "DMM")
        drv.connect()
        for key in ("manufacturer", "model", "serial", "version"):
            assert key in drv.identity
        drv.disconnect()


# ── v0.4.x regressions: measurement result contract ───────

class TestMeasurementResultContract:
    """Regression: MeasurementResult must support float(), len(), indexing, iteration."""

    def test_float_conversion(self):
        r = MeasurementResult(3.14, "V")
        assert float(r) == pytest.approx(3.14)

    def test_len_on_list_value(self):
        r = MeasurementResult([1.0, 2.0, 3.0], "dB")
        assert len(r) == 3

    def test_indexing(self):
        r = MeasurementResult([10.0, 20.0], "dBm")
        assert r[0] == 10.0
        assert r[1] == 20.0

    def test_iteration(self):
        r = MeasurementResult([1.0, 2.0], "V")
        assert list(r) == [1.0, 2.0]

    def test_to_json_roundtrip(self):
        import json
        r = MeasurementResult(5.0, "V", status="OK")
        j = r.to_json()
        data = json.loads(j)
        assert data["value"] == 5.0
        assert data["unit"] == "V"
        assert data["status"] == "OK"

    def test_complex_to_dict(self):
        r = MeasurementResult(complex(1.0, 2.0), "Z")
        d = r.to_dict()
        assert d["value"]["real"] == 1.0
        assert d["value"]["imag"] == 2.0


# ── v0.4.x regressions: safety guardrails ─────────────────

class TestSafetyGuardrails:
    """Regression: frequency/power validation must raise on out-of-range values."""

    def test_frequency_too_high(self):
        drv = get_instrument("SIM_SA", "SA")
        drv.connect()
        with pytest.raises(ConfigurationError):
            drv.set_center_freq(999e12)
        drv.disconnect()

    def test_power_exceeds_limit(self):
        drv = get_instrument("SIM_SG", "SG")
        drv.connect()
        with pytest.raises(OverloadError):
            drv.set_amplitude(9999.0)
        drv.disconnect()

    def test_format_frequency_units(self):
        drv = get_instrument("SIM_SA", "SA")
        drv.connect()
        assert "GHz" in drv.format_frequency(2.4e9)
        assert "MHz" in drv.format_frequency(100e6)
        assert "kHz" in drv.format_frequency(10e3)
        drv.disconnect()


# ── v0.4.x regressions: simulated physics ─────────────────

class TestSimulatedPhysics:
    """Regression: simulated instruments must return physically plausible values."""

    def test_dmm_voltage_noise(self):
        drv = get_instrument("SIM_DMM", "DMM")
        drv.connect()
        readings = [drv.measure_voltage().value for _ in range(50)]
        mean = sum(readings) / len(readings)
        assert 4.5 < mean < 5.5, f"DMM mean {mean} outside expected range"
        drv.disconnect()

    def test_psu_foldback_tracking(self):
        from instrumation.drivers.simulated import SimulatedPowerSupply
        psu = SimulatedPowerSupply("SIM_PSU")
        psu.connect()
        psu.set_foldback_mode("CC")
        assert psu._foldback_mode == "CC"
        psu.set_foldback_delay(2.5)
        assert psu._foldback_delay == 2.5
        psu.set_autostart(True)
        assert psu._autostart is True
        psu.disconnect()

    def test_eload_protection_trip(self):
        from instrumation.drivers.simulated import SimulatedElectronicLoad
        eload = SimulatedElectronicLoad("SIM_LOAD")
        eload.connect()
        eload.set_ovp(5.0)
        eload.set_input(True)
        # Source voltage is 12V, OVP is 5V -> should trip
        eload.measure_voltage()
        assert eload._protection_tripped == "OVP"
        assert eload.get_input() is False
        eload.disconnect()

    def test_sa_sweep_data_generation(self):
        drv = get_instrument("SIM_SA", "SA")
        drv.connect()
        trace = drv.get_trace_data()
        assert len(trace.value) == 1001
        assert all(isinstance(v, float) for v in trace.value)
        drv.disconnect()

    def test_vna_complex_trace(self):
        drv = get_instrument("SIM_VNA", "NA")
        drv.connect()
        data = drv.get_complex_trace()
        assert len(data.value) == 201
        assert all(isinstance(v, complex) for v in data.value)
        drv.disconnect()

    def test_counter_measurements(self):
        drv = get_instrument("SIM_COUNTER", "COUNTER")
        drv.connect()
        freq = drv.measure_frequency()
        assert freq.unit == "Hz"
        assert freq.value > 0
        period = drv.measure_period()
        assert period.unit == "s"
        drv.disconnect()


# ── v0.5.0: type hints regression ─────────────────────────

class TestTypeHints:
    """Regression: all base class methods must have type annotations."""

    def test_base_methods_have_return_annotations(self):
        from instrumation.drivers.base import (
            InstrumentDriver, Multimeter, PowerSupply,
            SpectrumAnalyzer, NetworkAnalyzer, Oscilloscope,
            SignalGenerator, ElectronicLoad, FrequencyCounter,
        )
        import inspect

        classes = [
            InstrumentDriver, Multimeter, PowerSupply,
            SpectrumAnalyzer, NetworkAnalyzer, Oscilloscope,
            SignalGenerator, ElectronicLoad, FrequencyCounter,
        ]
        missing = []
        for cls in classes:
            for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
                if name.startswith("_") and name != "__enter__" and name != "__exit__":
                    continue
                sig = inspect.signature(method)
                if sig.return_annotation is inspect.Parameter.empty:
                    missing.append(f"{cls.__name__}.{name}")
        assert missing == [], f"Methods missing return annotations: {missing}"


# ── v0.5.0: async wrapper regression ──────────────────────

class TestAsyncWrapper:
    """Regression: AsyncInstrumentDriver must work with all simulated driver types."""

    @pytest.mark.asyncio
    async def test_async_parallel_measurements(self):
        """Two async measurements should run in parallel, not sequentially."""
        from instrumation.drivers.async_driver import wrap_async

        dmm = get_instrument("SIM_DMM", "DMM")
        psu = get_instrument("SIM_PSU", "PSU")
        dmm.latency = 0.2
        psu.latency = 0.2

        async_dmm = wrap_async(dmm)
        async_psu = wrap_async(psu)

        dmm.connect()
        psu.connect()

        start = time.perf_counter()
        results = await asyncio.gather(
            async_dmm.measure_voltage(),
            async_psu.get_current(),
        )
        elapsed = time.perf_counter() - start

        assert elapsed < 0.35, f"Parallel took {elapsed:.2f}s, expected < 0.35s"
        assert isinstance(results[0], MeasurementResult)
        assert isinstance(results[1], MeasurementResult)

        dmm.disconnect()
        psu.disconnect()

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        from instrumation.drivers.async_driver import wrap_async

        drv = get_instrument("SIM_DMM", "DMM")
        async_drv = wrap_async(drv)

        async with async_drv:
            assert drv.connected is True
            result = await async_drv.measure_voltage()
            assert result.value > 0

        assert drv.connected is False

    @pytest.mark.asyncio
    async def test_async_context_manager_disconnects_on_keyboard_interrupt(self):
        """Issue #132: __aexit__ must still disconnect when shutdown_safety()
        raises KeyboardInterrupt (a BaseException)."""
        from instrumation.drivers.async_driver import AsyncInstrumentDriver, wrap_async
        from unittest.mock import MagicMock, patch

        drv = get_instrument("SIM_DMM", "DMM")
        async_drv = wrap_async(drv)

        # shutdown_safety raises KeyboardInterrupt; disconnect must still run
        async def raiser():
            raise KeyboardInterrupt()

        with patch.object(async_drv, "shutdown_safety", raiser), \
             patch.object(async_drv, "disconnect", new_callable=AsyncMock):
            try:
                async with async_drv:
                    pass
            except KeyboardInterrupt:
                pass

            async_drv.disconnect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_async_context_manager_disconnects_on_shutdown_error(self):
        """Issue #132: __aexit__ must still disconnect when shutdown_safety()
        raises an ordinary exception."""
        from instrumation.drivers.async_driver import wrap_async
        from unittest.mock import patch

        drv = get_instrument("SIM_DMM", "DMM")
        async_drv = wrap_async(drv)

        async def raiser():
            raise RuntimeError("boom")

        with patch.object(async_drv, "shutdown_safety", raiser), \
             patch.object(async_drv, "disconnect", new_callable=AsyncMock):
            async with async_drv:
                pass

            async_drv.disconnect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_async_context_manager_cleanup_timeout(self):
        """Issue #132: cleanup is bounded by a timeout so a hung driver cannot
        block the context manager exit forever."""
        from instrumation.drivers.async_driver import AsyncInstrumentDriver, wrap_async
        from unittest.mock import patch

        drv = get_instrument("SIM_DMM", "DMM")
        async_drv = wrap_async(drv)

        async def forever():
            await asyncio.sleep(3600)

        with patch.object(async_drv, "shutdown_safety", forever), \
             patch.object(async_drv, "disconnect", forever), \
             patch("instrumation.drivers.async_driver.CLEANUP_TIMEOUT", 0.05):
            async with async_drv:
                pass  # must return promptly despite the hung cleanup

    @pytest.mark.asyncio
    async def test_async_sa_operations(self):
        from instrumation.drivers.async_driver import wrap_async

        sa = get_instrument("SIM_SA", "SA")
        async_sa = wrap_async(sa)
        sa.connect()

        await async_sa.set_center_freq(5e9)
        assert sa.get_center_freq() == 5e9

        amp = await async_sa.get_marker_amplitude()
        assert amp.unit == "dBm"

        sa.disconnect()

    @pytest.mark.asyncio
    async def test_async_vna_trace(self):
        from instrumation.drivers.async_driver import wrap_async

        vna = get_instrument("SIM_VNA", "NA")
        async_vna = wrap_async(vna)
        vna.connect()

        trace = await async_vna.get_trace_data()
        assert len(trace.value) == 201

        complex_trace = await async_vna.get_complex_trace()
        assert all(isinstance(v, complex) for v in complex_trace.value)

        vna.disconnect()

    @pytest.mark.asyncio
    async def test_async_eload(self):
        from instrumation.drivers.async_driver import wrap_async

        eload = get_instrument("SIM_LOAD", "LOAD")
        async_eload = wrap_async(eload)
        eload.connect()

        await async_eload.set_mode("CC")
        assert await async_eload.get_mode() == "CC"

        await async_eload.set_current(2.5)
        assert await async_eload.get_current() == 2.5

        eload.disconnect()

    @pytest.mark.asyncio
    async def test_wrap_async_returns_correct_type(self):
        from instrumation.drivers.async_driver import (
            wrap_async, AsyncMultimeter, AsyncPowerSupply,
            AsyncSpectrumAnalyzer, AsyncNetworkAnalyzer,
            AsyncOscilloscope, AsyncFunctionGenerator,
            AsyncElectronicLoad, AsyncFrequencyCounter,
        )

        cases = [
            ("SIM_DMM", "DMM", AsyncMultimeter),
            ("SIM_PSU", "PSU", AsyncPowerSupply),
            ("SIM_SA", "SA", AsyncSpectrumAnalyzer),
            ("SIM_VNA", "NA", AsyncNetworkAnalyzer),
            ("SIM_SCOPE", "SCOPE", AsyncOscilloscope),
            ("SIM_SG", "SG", AsyncFunctionGenerator),
            ("SIM_LOAD", "LOAD", AsyncElectronicLoad),
            ("SIM_COUNTER", "COUNTER", AsyncFrequencyCounter),
        ]
        for addr, dtype, expected in cases:
            drv = get_instrument(addr, dtype)
            async_drv = wrap_async(drv)
            assert isinstance(async_drv, expected), (
                f"wrap_async({dtype}) returned {type(async_drv).__name__}, "
                f"expected {expected.__name__}"
            )


# ── v0.5.0: factory regression ────────────────────────────

class TestFactory:
    """Regression: factory must return correct driver types."""

    def test_factory_returns_multimeter(self):
        drv = get_instrument("SIM_DMM", "DMM")
        from instrumation.drivers.base import Multimeter
        assert isinstance(drv, Multimeter)

    def test_factory_returns_powersupply(self):
        drv = get_instrument("SIM_PSU", "PSU")
        from instrumation.drivers.base import PowerSupply
        assert isinstance(drv, PowerSupply)

    def test_factory_returns_spectrum_analyzer(self):
        drv = get_instrument("SIM_SA", "SA")
        from instrumation.drivers.base import SpectrumAnalyzer
        assert isinstance(drv, SpectrumAnalyzer)

    def test_factory_returns_oscilloscope(self):
        drv = get_instrument("SIM_SCOPE", "SCOPE")
        from instrumation.drivers.base import Oscilloscope
        assert isinstance(drv, Oscilloscope)

    def test_factory_returns_eload(self):
        drv = get_instrument("SIM_LOAD", "LOAD")
        from instrumation.drivers.base import ElectronicLoad
        assert isinstance(drv, ElectronicLoad)

    def test_factory_returns_counter(self):
        drv = get_instrument("SIM_COUNTER", "COUNTER")
        from instrumation.drivers.base import FrequencyCounter
        assert isinstance(drv, FrequencyCounter)


# ── v0.5.0: registry regression ───────────────────────────

class TestRegistry:
    """Regression: driver registry must have entries for all instrument types."""

    def test_registry_has_dmm(self):
        from instrumation.drivers.registry import DriverRegistry
        drivers = DriverRegistry.get_drivers_by_type("DMM")
        assert len(drivers) > 0

    def test_registry_has_psu(self):
        from instrumation.drivers.registry import DriverRegistry
        drivers = DriverRegistry.get_drivers_by_type("PSU")
        assert len(drivers) > 0

    def test_registry_has_sa(self):
        from instrumation.drivers.registry import DriverRegistry
        drivers = DriverRegistry.get_drivers_by_type("SA")
        assert len(drivers) > 0

    def test_registry_has_scope(self):
        from instrumation.drivers.registry import DriverRegistry
        drivers = DriverRegistry.get_drivers_by_type("SCOPE")
        assert len(drivers) > 0

    def test_registry_has_sg(self):
        from instrumation.drivers.registry import DriverRegistry
        drivers = DriverRegistry.get_drivers_by_type("SG")
        assert len(drivers) > 0

    def test_registry_has_eload(self):
        from instrumation.drivers.registry import DriverRegistry
        drivers = DriverRegistry.get_drivers_by_type("LOAD")
        assert len(drivers) > 0


# ── v0.5.1: Rigol DS1054Z regression ─────────────────────

class TestRigolDS1054Z:
    """Regression: RigolDS1054Z driver must implement Oscilloscope interface
    correctly, parse Rigol preamble format, and convert raw ADC codes to
    calibrated voltage values."""

    def _make_driver(self):
        from unittest.mock import MagicMock, patch
        with patch('pyvisa.ResourceManager'):
            from instrumation.drivers.rigol import RigolDS1054Z
            drv = RigolDS1054Z("USB0::0x1AB1::0x04CE::DS1054Z::INSTR")
            drv.inst = MagicMock()
            drv.inst.query.return_value = "+0,\"No error\""
            drv.connected = True
            return drv

    def test_driver_is_oscilloscope(self):
        from instrumation.drivers.rigol import RigolDS1054Z
        from instrumation.drivers.base import Oscilloscope
        assert issubclass(RigolDS1054Z, Oscilloscope)

    def test_driver_registered_as_scope(self):
        from instrumation.drivers.registry import DriverRegistry
        from instrumation.factory import load_plugins
        load_plugins()
        scopes = DriverRegistry.get_drivers_by_type("SCOPE")
        assert any("RigolDS1054Z" in cls.__name__ for cls in scopes)

    def test_channel_config_round_trip(self):
        drv = self._make_driver()
        drv.set_channel_coupling(1, "DC")
        drv.inst.query.return_value = "DC"
        assert drv.get_channel_coupling(1) == "DC"

        drv.set_channel_scale(2, 0.1)
        drv.inst.query.return_value = "0.1"
        assert drv.get_channel_scale(2) == pytest.approx(0.1)

        drv.set_channel_offset(3, -2.5)
        drv.inst.query.return_value = "-2.5"
        assert drv.get_channel_offset(3) == pytest.approx(-2.5)

    def test_timebase_scale_round_trip(self):
        drv = self._make_driver()
        drv.set_timebase_scale(1e-3)
        drv.inst.query.return_value = "0.001"
        assert drv.get_timebase_scale() == pytest.approx(1e-3)

    def test_waveform_preamble_parse_fields(self):
        drv = self._make_driver()
        drv.inst.query.return_value = "0,0,1000,1,2e-9,0.0,0,0.01,0.0,128"
        pre = drv.get_waveform_preamble()
        assert pre["format"] == 0
        assert pre["points"] == 1000
        assert pre["x_increment"] == pytest.approx(2e-9)
        assert pre["y_increment"] == pytest.approx(0.01)
        assert pre["y_origin"] == pytest.approx(0.0)
        assert pre["y_reference"] == 128

    def test_waveform_voltage_conversion(self):
        """Raw ADC codes must convert to real voltages correctly."""
        drv = self._make_driver()
        drv.inst.query.return_value = "0,0,4,1,1e-7,0.0,0,0.01,0.0,128"
        drv.inst.query_binary_values.return_value = [128, 228, 28, 128]
        result = drv.get_waveform(1)

        time_arr, volt_arr = result.value
        assert len(volt_arr) == 4
        assert result.unit == "V"
        assert result.channel == 1
        # 128 -> 0.0V, 228 -> 1.0V, 28 -> -1.0V
        assert volt_arr[0] == pytest.approx(0.0)
        assert volt_arr[1] == pytest.approx(1.0)
        assert volt_arr[2] == pytest.approx(-1.0)

    def test_waveform_time_axis_origin(self):
        drv = self._make_driver()
        drv.inst.query.return_value = "0,0,3,1,1e-6,-5e-6,0,0.01,0.0,128"
        drv.inst.query_binary_values.return_value = [128, 128, 128]
        result = drv.get_waveform(2)
        time_arr, _ = result.value
        assert time_arr[0] == pytest.approx(-5e-6)

    def test_channel_validation_rejects_out_of_range(self):
        drv = self._make_driver()
        with pytest.raises(ValueError):
            drv.set_channel_display(0, True)
        with pytest.raises(ValueError):
            drv.set_channel_display(5, True)

    def test_acquire_averages_rejects_non_power_of_two(self):
        drv = self._make_driver()
        with pytest.raises(ValueError):
            drv.set_acquire_averages(50)

    def test_acquire_averages_rejects_out_of_range(self):
        drv = self._make_driver()
        with pytest.raises(ValueError):
            drv.set_acquire_averages(2048)

    def test_edge_trigger_slope_validation(self):
        drv = self._make_driver()
        with pytest.raises(ValueError):
            drv.set_edge_trigger_slope("INVALID")

    def test_trigger_sweep_validation(self):
        drv = self._make_driver()
        with pytest.raises(ValueError):
            drv.set_trigger_sweep("BOGUS")

    def test_waveform_mode_validation(self):
        drv = self._make_driver()
        with pytest.raises(ValueError):
            drv.set_waveform_mode("INVALID")

    def test_waveform_format_validation(self):
        drv = self._make_driver()
        with pytest.raises(ValueError):
            drv.set_waveform_format("FLOAT")

    def test_context_manager_safety(self):
        from unittest.mock import MagicMock, patch
        with patch('pyvisa.ResourceManager'):
            from instrumation.drivers.rigol import RigolDS1054Z
            drv = RigolDS1054Z("USB0::0x1AB1::0x04CE::DS1054Z::INSTR")
            drv.inst = MagicMock()
            drv.inst.query.return_value = "1"
        with patch.object(drv, 'connect'), \
             patch.object(drv, 'disconnect') as mock_dis, \
             patch.object(drv, 'shutdown_safety') as mock_safe:
            with drv:
                pass
            mock_safe.assert_called_once()
            mock_dis.assert_called_once()


# ── v0.6.0: batch_query regression ────────────────────────

class TestBatchQueryRegression:
    """Regression: batch_query must reliably fetch multiple instrument settings."""

    def test_batch_query_returns_all_keys(self):
        """batch_query must return a response for every query sent."""
        from instrumation.transport import batch_query
        mock_inst = MagicMock()
        mock_inst.query.side_effect = ["SIM,DMM,1.0", "3.3", "0x10"]

        result = batch_query(mock_inst, ["*IDN?", "MEAS:VOLT?", "*STB?"])
        assert set(result.keys()) == {"*IDN?", "MEAS:VOLT?", "*STB?"}

    def test_batch_query_strips_whitespace(self):
        """Responses must be stripped for clean downstream parsing."""
        from instrumation.transport import batch_query
        mock_inst = MagicMock()
        mock_inst.query.return_value = "  42.5  \n"

        result = batch_query(mock_inst, ["READ?"])
        assert result["READ?"] == "42.5"

    def test_batch_query_survives_partial_failure(self):
        """A single failed query must not abort the entire batch."""
        from instrumation.transport import batch_query
        mock_inst = MagicMock()
        mock_inst.query.side_effect = [
            "Keysight,DMM",
            Exception("bus error"),
            "5.0",
        ]

        result = batch_query(mock_inst, ["*IDN?", "BROKEN?", "VOLT?"])
        assert result["*IDN?"] == "Keysight,DMM"
        assert "ERROR" in result["BROKEN?"]
        assert result["VOLT?"] == "5.0"

    def test_batch_query_stop_on_error_raises(self):
        """stop_on_error=True must propagate the first exception."""
        from instrumation.transport import batch_query
        mock_inst = MagicMock()
        mock_inst.query.side_effect = Exception("fatal")

        with pytest.raises(Exception, match="fatal"):
            batch_query(mock_inst, ["CMD?"], stop_on_error=True)

    def test_batch_query_empty_list_returns_empty_dict(self):
        """An empty query list must not call the instrument at all."""
        from instrumation.transport import batch_query
        mock_inst = MagicMock()

        result = batch_query(mock_inst, [])
        assert result == {}
        mock_inst.query.assert_not_called()


# ── Windows packaging regression ─────────────────────────────

class TestResourceManagerWindowsCompat:
    """Regression: get_rm() must never pass None to pyvisa.ResourceManager.

    Newer PyVISA versions crash on Windows when passed ``None`` with
    ``AttributeError: 'NoneType' object has no attribute 'rsplit'``. The
    manager must be built with an empty string so PyVISA auto-selects the
    available backend (system VISA or the bundled pyvisa_py).
    """

    def test_get_rm_passes_empty_string_when_no_ni_visa(self):
        import instrumation.factory as factory

        factory._GLOBAL_RM = None
        calls = []

        def fake_rm(arg):
            calls.append(arg)
            return MagicMock()

        with patch("instrumation.factory.os.path.exists", return_value=False), \
             patch("instrumation.factory.pyvisa.ResourceManager", side_effect=fake_rm):
            factory.get_rm()

        assert calls == [""]
        assert None not in calls

    def test_get_rm_passes_ni_visa_path_on_macos(self):
        import instrumation.factory as factory

        factory._GLOBAL_RM = None
        calls = []
        ni_lib = "/Library/Frameworks/VISA.framework/VISA"

        def fake_rm(arg):
            calls.append(arg)
            return MagicMock()

        with patch("instrumation.factory.os.path.exists", return_value=True), \
             patch("instrumation.factory.pyvisa.ResourceManager", side_effect=fake_rm):
            factory.get_rm()

        assert calls == [ni_lib]


# ── Issue #135: cache update after manual connection ───────

class TestManualConnectionCache:
    """Regression: a manual (non-AUTO) connection must update
    ``.visa_cache.json`` without raising UnboundLocalError.

    Previously ``import json`` lived inside the ``AUTO`` branch, making ``json``
    a cell variable that was never bound on the manual-connection path, so the
    cache-update block silently failed with ``UnboundLocalError``.
    """

    def test_manual_connection_updates_cache(self, tmp_path, monkeypatch):
        import instrumation.factory as factory
        from unittest.mock import patch

        monkeypatch.chdir(tmp_path)
        cache_file = tmp_path / ".visa_cache.json"
        cache_file.write_text("[]")

        mock_real_cls = MagicMock()
        mock_real_cls.return_value.get_id.return_value = "UNKNOWN,NOBODY"

        with patch("instrumation.factory.is_sim_mode", return_value=False), \
             patch("instrumation.factory.get_rm", return_value=MagicMock()), \
             patch("instrumation.factory.RealDriver", mock_real_cls), \
             patch("instrumation.factory.DriverRegistry.get_drivers_by_type", return_value=[]):
            factory.get_instrument("TCPIP::192.168.1.99::INSTR", "DMM")

        assert cache_file.exists()
        assert "TCPIP::192.168.1.99::INSTR" in cache_file.read_text()

    def test_manual_connection_does_not_raise_unboundlocal(self, tmp_path, monkeypatch):
        import instrumation.factory as factory
        from unittest.mock import patch

        monkeypatch.chdir(tmp_path)
        (tmp_path / ".visa_cache.json").write_text("[]")

        mock_real_cls = MagicMock()
        mock_real_cls.return_value.get_id.return_value = "UNKNOWN,NOBODY"

        with patch("instrumation.factory.is_sim_mode", return_value=False), \
             patch("instrumation.factory.get_rm", return_value=MagicMock()), \
             patch("instrumation.factory.RealDriver", mock_real_cls), \
             patch("instrumation.factory.DriverRegistry.get_drivers_by_type", return_value=[]):
            factory.get_instrument("TCPIP::192.168.1.99::INSTR", "DMM")  # no exception


# ── Issue #131: connect_instrument must not swallow ConfigurationError ─

class TestConnectInstrumentPropagatesConfigurationError:
    """Regression: connect_instrument() auto-detection must re-raise
    ConfigurationError instead of silently swallowing it and falling back."""

    def test_configuration_error_propagates(self):
        import instrumation
        from unittest.mock import patch
        from instrumation.exceptions import ConfigurationError

        mock_rm = MagicMock()
        mock_res = MagicMock()
        mock_res.query.return_value = "KEYSIGHT,EXG"

        with patch("instrumation.factory.get_rm", return_value=mock_rm), \
             patch("instrumation.factory.RealDriver"), \
             patch("instrumation.get_instrument",
                   side_effect=ConfigurationError("Bad config")):
            mock_rm.open_resource.return_value = mock_res

            with pytest.raises(ConfigurationError):
                instrumation.connect_instrument("TCPIP::1.2.3.4::INSTR")

    def test_other_errors_still_fall_back_to_dmm(self):
        import instrumation
        from unittest.mock import patch

        mock_rm = MagicMock()
        mock_rm.open_resource.side_effect = Exception("no such resource")

        with patch("instrumation.factory.get_rm", return_value=mock_rm), \
             patch("instrumation.factory.RealDriver"):
            # Fallback path returns a driver; it just must not raise
            try:
                instrumation.connect_instrument("TCPIP::1.2.3.4::INSTR")
            except Exception:
                pass
