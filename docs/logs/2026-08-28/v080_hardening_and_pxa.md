# Log: v0.8.0 — PXA Expansion & Hardening Release

**Issues closed**: [#146](https://github.com/abduznik/instrumation/issues/146), [#152](https://github.com/abduznik/instrumation/issues/152), [#153](https://github.com/abduznik/instrumation/issues/153), [#156](https://github.com/abduznik/instrumation/issues/156)

## Overview

v0.8.0 lands the comprehensive Keysight PXA N9030A driver alongside a hardening pass across the station, transport, logging, and factory layers — plus a Python 3.9 CI restore that had quietly broken the whole test matrix.

## New Driver: Comprehensive Keysight PXA N9030A SCPI ([#169](https://github.com/abduznik/instrumation/pull/169))

`KeysightPXA` grew from 2 inherited methods to **29 PXA-specific methods** in `drivers/keysight.py`:

- **Measurement config (7)** — sweep type, detector, averaging, coupling, impedance
- **Advanced triggering (4)** — source, level, delay, slope
- **Enhanced markers (5)** — frequency, position, next peak, threshold, noise
- **Bandwidth & sweep (4)** — RBW auto, VBW ratio, sweep time, IF gain
- **Real-Time Spectrum Analysis (3)** — RTSA enable, capture bandwidth, spoiled regions
- **System queries (4)** — options, serial number, firmware, self-test

Covered by 83 new mock-based tests in `tests/test_pxa.py`; the 14 pre-existing Keysight tests stay green.

## Station & Transport Fixes

### Station.connect() idempotent ([#179](https://github.com/abduznik/instrumation/pull/179)) — closes [#156](https://github.com/abduznik/instrumation/issues/156)

`get_instrument()` already connects each driver before `Station._add_instrument` stores it, so `Station.connect()` calling `inst.connect()` again re-opened the VISA resource and re-ran `sync_config`/`_discover_identity`/`_discover_options`. `Station.connect()` now skips instruments whose `connected` flag is already set, making repeated `connect()` calls safe no-ops. Regression tests added in `tests/test_station.py` and `test_adversarial.py`.

### query_value returns None on failure ([#181](https://github.com/abduznik/instrumation/pull/181)) — closes [#153](https://github.com/abduznik/instrumation/issues/153)

`VisaDriver.query_value` previously returned `float 0.0` both when a query raised and when the driver never connected — making a failed read indistinguishable from a genuine 0.0 reading. It now returns `None`; the success path still returns a stripped `str`, so a real `0.0` reading survives as `"0.0"`. `UUTHandler.mes_voltage` handles the new `None` sentinel explicitly, and the signature is documented as `Optional[str]`. Four new tests in `tests/test_transport_utils.py`.

## Logging & Diagnostics

### _unsupported_feature routes through logging ([#178](https://github.com/abduznik/instrumation/pull/178)) — closes [#152](https://github.com/abduznik/instrumation/issues/152)

`InstrumentDriver._unsupported_feature()` emitted warnings via `print()`, bypassing logging configuration entirely — applications capturing log records never saw them. All 38 call sites across 7 driver files now route through a module-level logger (`drivers/base.py`) using `logger.warning()` with lazy `%`-formatting. Bonus fix: any falsy `model` now falls back to `'Instrument'` (the old default only fired on a missing key). Regression tests in `tests/test_unsupported_feature.py`.

- **DataBroadcaster send failures are logged** — `utils.py` logs failed UDP broadcasts and warns after N consecutive failures instead of failing silently (`tests/test_broadcaster.py`).
- **Accurate `UUTHandler` deprecation notice** — `device.py` now points to the correct replacement class name.

## Configuration

`get_config()` in `config.py` now loads JSON/YAML config files with precedence *environment variables > config file > built-in defaults*. Config files are located via the `INSTRUMATION_CONFIG` env var, or `instrumation.json` / `instrumation.yaml` / `instrumation.yml` in the current directory or the user's home directory. YAML needs PyYAML (a clear error is raised if missing); JSON is stdlib-only. 110 lines of new tests in `tests/test_config.py`.

## Driver & Factory Hardening

- **Real mode fails loudly for unknown driver types** ([#146](https://github.com/abduznik/instrumation/issues/146)) — `get_instrument()` raises `ValueError` when `driver_type` is neither registered nor a canonical category (e.g. `SIM`), mirroring SIM mode's loud failure, instead of silently falling back to `GENERIC`.
- **Abstract contract enforced** — `safe_send`, `query_ascii`, and `query_binary_values` are now abstract on `InstrumentDriver`, and the async wrappers are validated against the sync signatures (`tests/test_async_wrapper_validation.py`).
- **`check_errors` Mock hack removed** — `RealDriver.check_errors` detects simulated drivers robustly instead of string-matching a mocked class name (`tests/test_check_errors.py`).
- **ASRL port parsing fixed** — `factory._skip_serial_probe` parses the numeric port from an exact `ASRLn::INSTR` match, so `ASRL10` and digits inside TCPIP addresses are no longer misclassified as legacy ports 1-4 (`tests/test_serial_probe_filter.py`).
- **Scanner catches same-description conflicts** — `find_duplicate_addresses` keys identities on `(type, desc)`, so two genuinely different devices sharing a description string are still reported (`tests/test_scanner.py`).

## CI (Python 3.9 restore) ([#182](https://github.com/abduznik/instrumation/pull/182))

- `config.py:44` used PEP 604 union syntax (`-> Path | None`) which is evaluated at runtime on Python 3.9 and raised `TypeError` at collection — fail-fast cancelled the rest of the matrix. Fixed with `from __future__ import annotations` (lazy annotations, 3.9-safe, no behavior change).
- The abstract-method change exposed that `ReplayDriver` was **un-instantiable** (`TypeError: Can't instantiate abstract class ... query_binary_values`). Implemented `ReplayDriver.query_binary_values` replay-style, mirroring `query_ascii` and parsing comma-separated floats — restoring the golden-master tests on every Python version.
- Removed the duplicate `.github/workflows/publish-pypi.yml` workflow; release bumped to **v0.8.0**.

## Test Count

Total: **496 tests passing** (up from 458 at the start of this cycle; baseline 492/492 on Python 3.9 and 3.11 after the CI fix).