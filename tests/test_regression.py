"""Regression tests for instrumation v0.5.0.

These tests guard against known behaviors and edge cases that have been
fixed or introduced across releases. If a regression test fails, something
that used to work has broken.
"""

import asyncio
import math
import os
import time

import pytest

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
