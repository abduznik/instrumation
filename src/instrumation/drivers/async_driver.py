"""Async wrapper for instrument drivers.

Provides explicit async versions of all measurement and control methods,
enabling parallel measurements across multiple instruments using asyncio.

Usage:
    from instrumation.drivers.async_driver import AsyncInstrumentDriver

    dmm = get_instrument("DMM_ADDR", "DMM")
    async_dmm = AsyncInstrumentDriver(dmm)

    result = await async_dmm.measure_voltage()
"""

import asyncio
from typing import Any, List, Optional, Union

from ..results import MeasurementResult

# Timeout (seconds) applied to shutdown_safety() and disconnect() during
# async context-manager cleanup so a hung VISA call cannot block exit.
CLEANUP_TIMEOUT = 5.0
from .base import (
    InstrumentDriver,
    Multimeter,
    PowerSupply,
    SpectrumAnalyzer,
    NetworkAnalyzer,
    Oscilloscope,
    SignalGenerator,
    FunctionGenerator,
    ElectronicLoad,
    FrequencyCounter,
)


class AsyncInstrumentDriver:
    """Async wrapper around any synchronous InstrumentDriver.

    Delegates all calls to the underlying driver via asyncio.to_thread,
    making blocking SCPI I/O non-blocking in async contexts.
    """

    def __init__(self, driver: InstrumentDriver) -> None:
        self._driver = driver

    @property
    def driver(self) -> InstrumentDriver:
        """Access the underlying synchronous driver."""
        return self._driver

    def __getattr__(self, name: str) -> Any:
        """Proxy attribute access to the underlying driver for non-method attrs."""
        return getattr(self._driver, name)

    # ── Core I/O ──────────────────────────────────────────

    async def connect(self) -> None:
        await asyncio.to_thread(self._driver.connect)

    async def disconnect(self) -> None:
        await asyncio.to_thread(self._driver.disconnect)

    async def close(self) -> None:
        await asyncio.to_thread(self._driver.close)

    async def write(self, command: str) -> None:
        await asyncio.to_thread(self._driver.write, command)

    async def query(self, command: str) -> str:
        return await asyncio.to_thread(self._driver.query, command)

    async def safe_send(self, command: str) -> None:
        await asyncio.to_thread(self._driver.safe_send, command)

    async def query_ascii(self, command: str) -> str:
        return await asyncio.to_thread(self._driver.query_ascii, command)

    async def query_binary_values(
        self, command: str, datatype: str = "f", is_big_endian: bool = False
    ) -> List[float]:
        return await asyncio.to_thread(
            self._driver.query_binary_values, command, datatype, is_big_endian
        )

    # ── Global Logic & Synchronization ────────────────────

    async def get_id(self) -> str:
        return await asyncio.to_thread(self._driver.get_id)

    async def preset(self, automation_optimized: bool = True) -> None:
        await asyncio.to_thread(self._driver.preset, automation_optimized)

    async def clear_status(self) -> None:
        await asyncio.to_thread(self._driver.clear_status)

    async def sync_config(self) -> None:
        await asyncio.to_thread(self._driver.sync_config)

    async def wait_ready(self, timeout: float = 30.0) -> None:
        await asyncio.to_thread(self._driver.wait_ready, timeout)

    async def shutdown_safety(self) -> None:
        await asyncio.to_thread(self._driver.shutdown_safety)

    async def check_errors(self) -> None:
        await asyncio.to_thread(self._driver.check_errors)

    async def save_state(self, index: Union[int, str]) -> None:
        await asyncio.to_thread(self._driver.save_state, index)

    async def load_state(self, index: Union[int, str]) -> None:
        await asyncio.to_thread(self._driver.load_state, index)

    # ── Measurements ──────────────────────────────────────

    async def measure_frequency(self) -> MeasurementResult:
        return await asyncio.to_thread(self._driver.measure_frequency)

    async def measure_duty_cycle(self) -> MeasurementResult:
        return await asyncio.to_thread(self._driver.measure_duty_cycle)

    async def measure_v_peak_to_peak(self) -> MeasurementResult:
        return await asyncio.to_thread(self._driver.measure_v_peak_to_peak)

    # ── Context manager ───────────────────────────────────

    async def __aenter__(self) -> "AsyncInstrumentDriver":
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Any) -> None:
        # Cleanup must always run, even if shutdown_safety() raises a
        # KeyboardInterrupt (a BaseException that a bare except Exception
        # clause would not catch) — otherwise the VISA session leaks. Each
        # step is bounded with a timeout so a hung driver cannot block exit.
        try:
            try:
                await asyncio.wait_for(self.shutdown_safety(), timeout=CLEANUP_TIMEOUT)
            except BaseException:
                pass
        finally:
            try:
                await asyncio.wait_for(self.disconnect(), timeout=CLEANUP_TIMEOUT)
            except BaseException:
                pass


class AsyncMultimeter(AsyncInstrumentDriver):
    """Async wrapper for Multimeter drivers."""

    async def configure_voltage_dc(self) -> None:
        await asyncio.to_thread(self._driver.configure_voltage_dc)

    async def configure_voltage_ac(self) -> None:
        await asyncio.to_thread(self._driver.configure_voltage_ac)

    async def measure_voltage(self, ac: bool = False) -> MeasurementResult:
        return await asyncio.to_thread(self._driver.measure_voltage, ac)

    async def measure_resistance(self, four_wire: bool = False) -> MeasurementResult:
        return await asyncio.to_thread(self._driver.measure_resistance, four_wire)

    async def measure_current(self, ac: bool = False) -> MeasurementResult:
        return await asyncio.to_thread(self._driver.measure_current, ac)

    async def set_auto_range(self, state: bool) -> None:
        await asyncio.to_thread(self._driver.set_auto_range, state)


class AsyncPowerSupply(AsyncInstrumentDriver):
    """Async wrapper for PowerSupply drivers."""

    async def set_voltage(self, voltage: float) -> None:
        await asyncio.to_thread(self._driver.set_voltage, voltage)

    async def get_voltage(self) -> float:
        return await asyncio.to_thread(self._driver.get_voltage)

    async def set_current_limit(self, current: float) -> None:
        await asyncio.to_thread(self._driver.set_current_limit, current)

    async def set_current(self, current: float) -> None:
        await asyncio.to_thread(self._driver.set_current, current)

    async def get_current(self) -> MeasurementResult:
        return await asyncio.to_thread(self._driver.get_current)

    async def set_output(self, state: bool) -> None:
        await asyncio.to_thread(self._driver.set_output, state)

    async def get_output(self) -> bool:
        return await asyncio.to_thread(self._driver.get_output)

    async def set_ovp(self, voltage: float) -> None:
        await asyncio.to_thread(self._driver.set_ovp, voltage)

    async def set_ocp(self, current: float) -> None:
        await asyncio.to_thread(self._driver.set_ocp, current)

    async def measure_voltage_actual(self) -> MeasurementResult:
        return await asyncio.to_thread(self._driver.measure_voltage_actual)

    async def measure_voltage(self) -> MeasurementResult:
        return await asyncio.to_thread(self._driver.measure_voltage)

    async def measure_current(self) -> MeasurementResult:
        return await asyncio.to_thread(self._driver.measure_current)

    async def clear_protection(self) -> None:
        await asyncio.to_thread(self._driver.clear_protection)

    async def measure_power(self) -> MeasurementResult:
        return await asyncio.to_thread(self._driver.measure_power)

    async def set_foldback_mode(self, mode: str) -> None:
        await asyncio.to_thread(self._driver.set_foldback_mode, mode)

    async def set_foldback_delay(self, seconds: float) -> None:
        await asyncio.to_thread(self._driver.set_foldback_delay, seconds)

    async def set_autostart(self, state: bool) -> None:
        await asyncio.to_thread(self._driver.set_autostart, state)

    async def get_mode(self) -> str:
        return await asyncio.to_thread(self._driver.get_mode)


class AsyncSpectrumAnalyzer(AsyncInstrumentDriver):
    """Async wrapper for SpectrumAnalyzer drivers."""

    async def peak_search(self) -> None:
        await asyncio.to_thread(self._driver.peak_search)

    async def get_marker_amplitude(self) -> MeasurementResult:
        return await asyncio.to_thread(self._driver.get_marker_amplitude)

    async def set_center_freq(self, hz: float) -> None:
        await asyncio.to_thread(self._driver.set_center_freq, hz)

    async def get_center_freq(self) -> float:
        return await asyncio.to_thread(self._driver.get_center_freq)

    async def set_span(self, hz: float) -> None:
        await asyncio.to_thread(self._driver.set_span, hz)

    async def get_span(self) -> float:
        return await asyncio.to_thread(self._driver.get_span)

    async def set_rbw(self, hz: float) -> None:
        await asyncio.to_thread(self._driver.set_rbw, hz)

    async def set_vbw(self, hz: float) -> None:
        await asyncio.to_thread(self._driver.set_vbw, hz)

    async def get_trace_data(self) -> MeasurementResult:
        return await asyncio.to_thread(self._driver.get_trace_data)

    async def get_peak_value(self) -> MeasurementResult:
        return await asyncio.to_thread(self._driver.get_peak_value)


class AsyncNetworkAnalyzer(AsyncInstrumentDriver):
    """Async wrapper for NetworkAnalyzer drivers."""

    async def set_start_frequency(self, freq_hz: float) -> None:
        await asyncio.to_thread(self._driver.set_start_frequency, freq_hz)

    async def set_stop_frequency(self, freq_hz: float) -> None:
        await asyncio.to_thread(self._driver.set_stop_frequency, freq_hz)

    async def set_center_freq(self, freq_hz: float) -> None:
        await asyncio.to_thread(self._driver.set_center_freq, freq_hz)

    async def set_center_frequency(self, freq_hz: float) -> None:
        await asyncio.to_thread(self._driver.set_center_frequency, freq_hz)

    async def set_span(self, span_hz: float) -> None:
        await asyncio.to_thread(self._driver.set_span, span_hz)

    async def set_points(self, num_points: int) -> None:
        await asyncio.to_thread(self._driver.set_points, num_points)

    async def set_if_bandwidth(self, hz: float) -> None:
        await asyncio.to_thread(self._driver.set_if_bandwidth, hz)

    async def set_power_level(self, dbm: float) -> None:
        await asyncio.to_thread(self._driver.set_power_level, dbm)

    async def set_sweep_type(self, sweep_type: str) -> None:
        await asyncio.to_thread(self._driver.set_sweep_type, sweep_type)

    async def set_averaging(self, state: bool, count: int = 10) -> None:
        await asyncio.to_thread(self._driver.set_averaging, state, count)

    async def set_continuous(self, state: bool) -> None:
        await asyncio.to_thread(self._driver.set_continuous, state)

    async def set_parameter(self, parameter: str) -> None:
        await asyncio.to_thread(self._driver.set_parameter, parameter)

    async def get_trace_data(self, measurement_name: str = "CH1_S11_1") -> MeasurementResult:
        return await asyncio.to_thread(self._driver.get_trace_data, measurement_name)

    async def get_complex_trace(self, measurement_name: str = "CH1_S11_1") -> MeasurementResult:
        return await asyncio.to_thread(self._driver.get_complex_trace, measurement_name)

    async def get_smith_data(self, measurement_name: str = "CH1_S11_1") -> MeasurementResult:
        return await asyncio.to_thread(self._driver.get_smith_data, measurement_name)

    async def peak_search(self, marker: int = 1) -> None:
        await asyncio.to_thread(self._driver.peak_search, marker)

    async def get_marker_x(self, marker: int = 1) -> float:
        return await asyncio.to_thread(self._driver.get_marker_x, marker)

    async def get_marker_y(self, marker: int = 1) -> float:
        return await asyncio.to_thread(self._driver.get_marker_y, marker)

    async def save_state(self, filename: str) -> None:
        await asyncio.to_thread(self._driver.save_state, filename)

    async def load_state(self, filename: str) -> None:
        await asyncio.to_thread(self._driver.load_state, filename)

    async def wait_for_sweep(self) -> None:
        await asyncio.to_thread(self._driver.wait_for_sweep)


class AsyncOscilloscope(AsyncInstrumentDriver):
    """Async wrapper for Oscilloscope drivers."""

    async def run(self) -> None:
        await asyncio.to_thread(self._driver.run)

    async def stop(self) -> None:
        await asyncio.to_thread(self._driver.stop)

    async def single(self) -> None:
        await asyncio.to_thread(self._driver.single)

    async def get_waveform(self, channel: int) -> MeasurementResult:
        return await asyncio.to_thread(self._driver.get_waveform, channel)

    async def auto_scale(self) -> None:
        await asyncio.to_thread(self._driver.auto_scale)

    async def set_trigger(self, source: str, level: float, slope: str) -> None:
        await asyncio.to_thread(self._driver.set_trigger, source, level, slope)

    async def get_screenshot(self) -> bytes:
        return await asyncio.to_thread(self._driver.get_screenshot)

    async def measure_frequency(self, channel: int = 1) -> MeasurementResult:
        return await asyncio.to_thread(self._driver.measure_frequency, channel)

    async def measure_duty_cycle(self, channel: int = 1) -> MeasurementResult:
        return await asyncio.to_thread(self._driver.measure_duty_cycle, channel)

    async def measure_v_peak_to_peak(self, channel: int = 1) -> MeasurementResult:
        return await asyncio.to_thread(self._driver.measure_v_peak_to_peak, channel)


class AsyncSignalGenerator(AsyncInstrumentDriver):
    """Async wrapper for SignalGenerator drivers."""

    async def set_frequency(self, hz: float) -> None:
        await asyncio.to_thread(self._driver.set_frequency, hz)

    async def set_amplitude(self, dbm: float) -> None:
        await asyncio.to_thread(self._driver.set_amplitude, dbm)

    async def set_output(self, state: bool) -> None:
        await asyncio.to_thread(self._driver.set_output, state)

    async def set_mod_state(self, mod_type: str, state: bool) -> None:
        await asyncio.to_thread(self._driver.set_mod_state, mod_type, state)

    async def start_sweep(self, start: float, stop: float, points: int, dwell: float) -> None:
        await asyncio.to_thread(self._driver.start_sweep, start, stop, points, dwell)

    async def configure_list_sweep(self, freq_list: List[float], power_list: List[float]) -> None:
        await asyncio.to_thread(self._driver.configure_list_sweep, freq_list, power_list)

    async def set_reference_clock(self, source: str) -> None:
        await asyncio.to_thread(self._driver.set_reference_clock, source)


class AsyncFunctionGenerator(AsyncSignalGenerator):
    """Async wrapper for FunctionGenerator drivers."""

    async def set_voltage(self, vpp: float) -> None:
        await asyncio.to_thread(self._driver.set_voltage, vpp)

    async def set_offset(self, volts: float) -> None:
        await asyncio.to_thread(self._driver.set_offset, volts)

    async def set_waveform(self, shape: str) -> None:
        await asyncio.to_thread(self._driver.set_waveform, shape)


class AsyncElectronicLoad(AsyncInstrumentDriver):
    """Async wrapper for ElectronicLoad drivers."""

    async def set_mode(self, mode: str) -> None:
        await asyncio.to_thread(self._driver.set_mode, mode)

    async def get_mode(self) -> str:
        return await asyncio.to_thread(self._driver.get_mode)

    async def set_current(self, amps: float) -> None:
        await asyncio.to_thread(self._driver.set_current, amps)

    async def get_current(self) -> float:
        return await asyncio.to_thread(self._driver.get_current)

    async def set_voltage(self, volts: float) -> None:
        await asyncio.to_thread(self._driver.set_voltage, volts)

    async def get_voltage(self) -> float:
        return await asyncio.to_thread(self._driver.get_voltage)

    async def set_resistance(self, ohms: float) -> None:
        await asyncio.to_thread(self._driver.set_resistance, ohms)

    async def get_resistance(self) -> float:
        return await asyncio.to_thread(self._driver.get_resistance)

    async def set_power(self, watts: float) -> None:
        await asyncio.to_thread(self._driver.set_power, watts)

    async def get_power(self) -> float:
        return await asyncio.to_thread(self._driver.get_power)

    async def set_input(self, state: bool) -> None:
        await asyncio.to_thread(self._driver.set_input, state)

    async def get_input(self) -> bool:
        return await asyncio.to_thread(self._driver.get_input)

    async def measure_voltage(self) -> MeasurementResult:
        return await asyncio.to_thread(self._driver.measure_voltage)

    async def measure_current(self) -> MeasurementResult:
        return await asyncio.to_thread(self._driver.measure_current)

    async def measure_power(self) -> MeasurementResult:
        return await asyncio.to_thread(self._driver.measure_power)

    async def set_ovp(self, voltage: float) -> None:
        await asyncio.to_thread(self._driver.set_ovp, voltage)

    async def set_ocp(self, current: float) -> None:
        await asyncio.to_thread(self._driver.set_ocp, current)

    async def set_opp(self, power: float) -> None:
        await asyncio.to_thread(self._driver.set_opp, power)

    async def clear_protection(self) -> None:
        await asyncio.to_thread(self._driver.clear_protection)


class AsyncFrequencyCounter(AsyncInstrumentDriver):
    """Async wrapper for FrequencyCounter drivers."""

    async def measure_frequency(self, range: str = "AUTO") -> MeasurementResult:
        return await asyncio.to_thread(self._driver.measure_frequency, range)

    async def measure_period(self, range: str = "AUTO") -> MeasurementResult:
        return await asyncio.to_thread(self._driver.measure_period, range)

    async def measure_time_interval(self, start_trigger: str, stop_trigger: str) -> MeasurementResult:
        return await asyncio.to_thread(self._driver.measure_time_interval, start_trigger, stop_trigger)

    async def set_impedance(self, ohms: float) -> None:
        await asyncio.to_thread(self._driver.set_impedance, ohms)

    async def set_trigger_level(self, volts: float) -> None:
        await asyncio.to_thread(self._driver.set_trigger_level, volts)

    async def set_coupling(self, dc_ac: str) -> None:
        await asyncio.to_thread(self._driver.set_coupling, dc_ac)

    async def set_auto_range(self, state: bool) -> None:
        await asyncio.to_thread(self._driver.set_auto_range, state)


def wrap_async(driver: InstrumentDriver) -> AsyncInstrumentDriver:
    """Factory: wraps a synchronous driver in the appropriate async wrapper.

    Inspects the driver's MRO to pick the most specific async wrapper available.
    """
    from .base import (
        Multimeter,
        PowerSupply,
        SpectrumAnalyzer,
        NetworkAnalyzer,
        Oscilloscope,
        FunctionGenerator,
        SignalGenerator,
        ElectronicLoad,
        FrequencyCounter,
    )

    # Order matters: most specific first
    _WRAPPERS = [
        (FunctionGenerator, AsyncFunctionGenerator),
        (ElectronicLoad, AsyncElectronicLoad),
        (FrequencyCounter, AsyncFrequencyCounter),
        (Multimeter, AsyncMultimeter),
        (PowerSupply, AsyncPowerSupply),
        (SpectrumAnalyzer, AsyncSpectrumAnalyzer),
        (NetworkAnalyzer, AsyncNetworkAnalyzer),
        (Oscilloscope, AsyncOscilloscope),
        (SignalGenerator, AsyncSignalGenerator),
    ]

    for base_cls, wrapper_cls in _WRAPPERS:
        if isinstance(driver, base_cls):
            return wrapper_cls(driver)

    return AsyncInstrumentDriver(driver)
