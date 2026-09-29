"""Async wrapper for instrument drivers.

Every callable on the wrapped driver becomes a coroutine that runs the
blocking call in a worker thread via ``asyncio.to_thread``. All positional
and keyword arguments (e.g. ``channel=``) are forwarded unchanged, and
driver-specific methods work without a hand-written wrapper.

Usage:
    from instrumation.drivers.async_driver import wrap_async

    dmm = get_instrument("DMM_ADDR", "DMM")
    async_dmm = wrap_async(dmm)

    result = await async_dmm.measure_voltage()
"""

import asyncio
import functools
from typing import Any, Optional

from .base import InstrumentDriver

# Timeout (seconds) applied to shutdown_safety() and disconnect() during
# async context-manager cleanup so a hung VISA call cannot block exit.
CLEANUP_TIMEOUT = 5.0


class AsyncInstrumentDriver:
    """Async proxy around any synchronous InstrumentDriver.

    Callable attributes are returned as ``async`` functions; non-callable
    attributes (``identity``, ``resource``, ...) are returned as-is.
    """

    def __init__(self, driver: InstrumentDriver) -> None:
        self._driver = driver

    @property
    def driver(self) -> InstrumentDriver:
        """Access the underlying synchronous driver."""
        return self._driver

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._driver, name)
        if not callable(attr):
            return attr

        @functools.wraps(attr)
        async def call(*args: Any, **kwargs: Any) -> Any:
            return await asyncio.to_thread(attr, *args, **kwargs)
        return call

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


# Backwards-compatible names: the per-category wrappers were identical
# thread-offloading shims, so they are all the generic proxy now.
AsyncMultimeter = AsyncPowerSupply = AsyncSpectrumAnalyzer = AsyncInstrumentDriver
AsyncNetworkAnalyzer = AsyncOscilloscope = AsyncSignalGenerator = AsyncInstrumentDriver
AsyncFunctionGenerator = AsyncElectronicLoad = AsyncFrequencyCounter = AsyncInstrumentDriver


def wrap_async(driver: InstrumentDriver) -> AsyncInstrumentDriver:
    """Wraps a synchronous driver in the async proxy."""
    return AsyncInstrumentDriver(driver)
