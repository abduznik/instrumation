# Log: v0.9.0 — Discovery Hardening & Legacy Cleanup

**Issues closed**: [#127](https://github.com/abduznik/instrumation/issues/127), [#130](https://github.com/abduznik/instrumation/issues/130), [#148](https://github.com/abduznik/instrumation/issues/148), [#149](https://github.com/abduznik/instrumation/issues/149), [#150](https://github.com/abduznik/instrumation/issues/150), [#158](https://github.com/abduznik/instrumation/issues/158), [#159](https://github.com/abduznik/instrumation/issues/159), [#160](https://github.com/abduznik/instrumation/issues/160), [#161](https://github.com/abduznik/instrumation/issues/161), [#163](https://github.com/abduznik/instrumation/issues/163), [#167](https://github.com/abduznik/instrumation/issues/167)

## Overview

v0.9.0 finishes the AUTO-discovery hardening pass started in v0.8.0, removes the long-deprecated `UUTHandler`, and closes out several documentation gaps flagged during the v0.8.0 bug bash.

## Cleanup: Deprecated `UUTHandler` Removed ([#127](https://github.com/abduznik/instrumation/issues/127))

`UUTHandler` in `src/instrumation/device.py` was deprecated since v0.2.0 with a warning promising removal in v0.3.0, and was still shipping at v0.8.0. `device.py` is now deleted, along with the top-level `connect()` convenience wrapper in `__init__.py` that existed solely to construct it. `search_devices()`/`scan()` are unaffected. `examples/common/my_test_bench.py` now demonstrates `transport.SerialDriver` used directly instead.

**Breaking change**: code importing `instrumation.UUTHandler` or calling `instrumation.connect()` must migrate to `factory.get_instrument()` (VISA) and `transport.SerialDriver` (serial) directly.

## VISA Resource Manager Lifecycle ([#161](https://github.com/abduznik/instrumation/issues/161))

Added `factory.close_rm()` to release the process-wide cached `pyvisa.ResourceManager`. Useful for long-running processes switching VISA backends, releasing the OS-level handle when instrument access is no longer needed, or giving tests full VISA-state isolation between runs. The next `get_rm()` call transparently recreates the manager.

## AUTO-Discovery & Transport Hardening (carried from the pre-release fix batch)

- **[#149](https://github.com/abduznik/instrumation/issues/149)** — IDN-probe exception handling narrowed to expected transport errors instead of a broad `except Exception`, so genuine programming errors surface loudly.
- **[#150](https://github.com/abduznik/instrumation/issues/150)** — TDK-Lambda's ASRL handshake is now gated to explicit connections; AUTO discovery no longer sends vendor-specific commands to arbitrary serial devices.
- **[#159](https://github.com/abduznik/instrumation/issues/159)** — AUTO-discovery candidate ordering now uses real transport priority tiers (LAN > USB > GPIB > serial) instead of a naive boolean sort key.
- **[#163](https://github.com/abduznik/instrumation/issues/163)** — `VisaDriver.write` harmonized with `query_value`'s forgiving error contract.
- **[#130](https://github.com/abduznik/instrumation/issues/130)** — `ReplayDriver` getters read golden-master responses with fallbacks.
- **[#160](https://github.com/abduznik/instrumation/issues/160)** — Simulated-driver filtering uses the explicit `is_simulated` class flag instead of fragile class-name string matching.

## Documentation

- **[#148](https://github.com/abduznik/instrumation/issues/148)** — `DriverRegistry`'s docstring now documents the canonical type-key concept and explicitly describes `"GENERIC"` as an always-registered fallback key; `docs/supported_instruments.md` gained a GENERIC section.
- **[#167](https://github.com/abduznik/instrumation/issues/167)** — `docs/supported_instruments.md` states the Validated/Assumed-compatible convention up front and documents `Keysight34461A`'s two distinct IDN-routed model families (Truevolt vs. legacy) with a per-model compatibility table, since only 34461A is verified against real hardware.
- **[#158](https://github.com/abduznik/instrumation/issues/158)** — `ROADMAP.md`'s bug table reconciled against actual code/issue state: corrected issue-number mappings, closed items that were still listed open, the v0.8.0/v0.9.0 fix batch, and the Dashboard section reframed as "Planned".

## Test Suite

521 → 517 tests (net -4 after removing `UUTHandler`-specific coverage that no longer applies), plus 3 new tests for `close_rm()`. Full suite green across Python 3.9–3.13.
