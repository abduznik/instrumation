## Key Features in v0.9.0

### Cleanup: Deprecated `UUTHandler` Removed (Issue #127)
- **`src/instrumation/device.py` deleted.** `UUTHandler` was deprecated since v0.2.0 with a warning promising removal in v0.3.0; it was still shipping at v0.8.0. It, and the top-level `connect()` convenience wrapper in `__init__.py` that existed only to construct it, are both gone.
- `search_devices()`/`scan()` are unaffected — they don't depend on `UUTHandler`. Use `factory.get_instrument()` / `Station` for VISA instruments and `transport.SerialDriver` directly for a serial box.
- `examples/common/my_test_bench.py` updated to use `SerialDriver` directly instead of `UUTHandler`.
- **Breaking change**: any code still importing `instrumation.UUTHandler` or calling `instrumation.connect()` must migrate to `factory.get_instrument()` (VISA) and `transport.SerialDriver` (serial) directly.

### VISA Resource Manager Lifecycle (Issue #161)
- **New `factory.close_rm()` API**: releases the process-wide cached `pyvisa.ResourceManager` created by `get_rm()`. Useful for long-running processes that need to switch VISA backends, release the OS-level VISA handle when instrument access is no longer needed, or give tests full isolation of VISA state between runs. Safe no-op if no resource manager has been created yet; the next `get_rm()` call transparently creates a fresh one.

### Documentation: Driver Compatibility Matrix (Issue #167)
- **`docs/supported_instruments.md`** now states the Validated/Assumed-compatible convention explicitly up front, and calls out `Keysight34461A`'s two distinct IDN-routed model families (Truevolt 34460/34461 vs. legacy 34401/34410/34411/34420) with a per-model compatibility table, since only 34461A has been verified against real hardware.

### Registry Discoverability (Issue #148)
- `DriverRegistry`'s docstring now documents the canonical type-key concept and explicitly describes `"GENERIC"` as an always-registered fallback key. `docs/supported_instruments.md` gained a GENERIC section.

### Roadmap Accuracy (Issue #158)
- `ROADMAP.md`'s bug table reconciled against actual code and issue state: corrected issue-number mappings, closed items that were still listed open, the v0.8.0/v0.9.0 fix batch, and the Dashboard section reframed as "Planned" (no dashboard module exists yet).

### Carried from the pre-release v0.9.0 fix batch
- **#149** — IDN-probe exception handling narrowed to expected transport errors instead of a broad `except Exception`.
- **#150** — TDK-Lambda ASRL handshake gated to explicit connections; AUTO discovery no longer sends vendor-specific commands to arbitrary serial devices.
- **#159** — AUTO-discovery candidate ordering now uses real transport priority tiers instead of a naive boolean sort key.
- **#163** — `VisaDriver.write` harmonized with `query_value`'s forgiving error contract.
- **#130** — `ReplayDriver` getters read golden-master responses with fallbacks.
- **#160** — Simulated-driver filtering uses the explicit `is_simulated` class flag instead of fragile class-name string matching.

---

## Key Features in v0.8.0

### New Driver: Comprehensive Keysight PXA N9030A SCPI (Issue #169)
- **29 new PXA-specific methods** in `drivers/keysight.py` (up from 2 inherited), making `KeysightPXA` a first-class spectrum analyzer driver:
  - *Measurement config (7)*: sweep type, detector, averaging, coupling, impedance
  - *Advanced triggering (4)*: source, level, delay, slope
  - *Enhanced markers (5)*: frequency, position, next peak, threshold, noise
  - *Bandwidth & sweep (4)*: RBW auto, VBW ratio, sweep time, IF gain
  - *Real-Time Spectrum Analysis (3)*: RTSA enable, capture bandwidth, spoiled regions
  - *System queries (4)*: options, serial number, firmware, self-test
- 83 new tests in `tests/test_pxa.py` with full mock coverage; all 14 existing Keysight tests remain green.

### Station & Transport Fixes (Issues #153, #156)
- **Issue #156 — `Station.connect()` no longer double-connects instruments**: `get_instrument()` already connects each driver before `Station._add_instrument()` stores it, so `Station.connect()` was redundantly calling `inst.connect()` again — re-opening the VISA resource and re-running `sync_config`/identity discovery. It now skips instruments whose `connected` flag is already set, making repeated `connect()` calls safe no-ops.
- **Issue #153 — `VisaDriver.query_value` no longer returns an ambiguous `0.0` on failure**: A failed query or a never-connected driver previously returned `float 0.0`, indistinguishable from a genuine zero reading. It now returns `None`; the success path still returns a stripped `str`, so a real `0.0` reading survives as `"0.0"`. `UUTHandler.mes_voltage` handles the new `None` sentinel explicitly, and the signature is documented as `Optional[str]`.

### Logging & Diagnostics (Issue #152)
- **Issue #152 — `_unsupported_feature` warnings now go through logging**: Driver warnings were emitted via `print()`, bypassing logging configuration entirely — applications capturing log records never saw them, and they couldn't be filtered or formatted. All 38 call sites across 7 driver files now route through a module-level logger using `logger.warning()` with lazy `%`-formatting.
- **DataBroadcaster send failures are logged**: `utils.py` now logs failed UDP broadcasts and warns after N consecutive failures instead of failing silently.
- **Accurate `UUTHandler` deprecation notice**: `device.py`'s deprecation message now points to the correct replacement instead of a misleading class name.

### Configuration
- **`get_config()` now loads JSON/YAML config files**: `config.get_config()` resolves values with precedence *environment variables > config file > built-in defaults*. Config files are located via the `INSTRUMATION_CONFIG` env var, or `instrumation.json` / `instrumation.yaml` / `instrumation.yml` in the current directory or the user's home directory. YAML requires PyYAML (a clear error is raised if it's missing); JSON works with the standard library only.

### Driver & Factory Hardening
- **Real mode fails loudly for unknown driver types (Issue #146)**: `get_instrument()` now raises `ValueError` when `driver_type` is neither a registered driver nor a canonical category (e.g. `SIM`), mirroring simulation mode's loud failure, instead of silently falling back to `GENERIC`.
- **Abstract contract enforced**: `safe_send`, `query_ascii`, and `query_binary_values` are now abstract on `InstrumentDriver`, and the async wrappers are validated against the sync signatures (`tests/test_async_wrapper_validation.py`). This immediately exposed that `ReplayDriver` was un-instantiable.
- **`check_errors` no longer relies on a Mock class-name hack**: `RealDriver.check_errors` now detects simulated drivers robustly instead of string-matching a mocked class name (`tests/test_check_errors.py`).
- **ASRL port parsing fixed**: `factory._skip_serial_probe` now parses the numeric port from an exact `ASRLn::INSTR` match instead of a naive substring skip, so `ASRL10` and digits inside TCPIP addresses are no longer misclassified as low-numbered legacy ports (`tests/test_serial_probe_filter.py`).
- **Scanner detects same-address conflicts with identical descriptions**: `find_duplicate_addresses` now keys identities on `(type, desc)`, so two genuinely different devices that happen to share a description string are still reported (`tests/test_scanner.py`).

### CI (Issue #182)
- **Python 3.9 compatibility restored**: `config.py` used PEP 604 union syntax (`-> Path | None`) which raises `TypeError` at import time on Python 3.9; a `from __future__ import annotations` import makes it 3.9-safe with no behavior change.
- **`ReplayDriver.query_binary_values` implemented**: the abstract-method change exposed that `ReplayDriver` couldn't be instantiated at all (breaking the golden-master tests); it now replays comma-separated floats, mirroring `query_ascii`.
- Removed the duplicate `.github/workflows/publish-pypi.yml` workflow and bumped the release to **v0.8.0**.

### Bug Fixes: Generic/Fallback Instrument Driver Wired Up (Issues #142-#145, #147)
- **Issue #142 — `GenericDriver`/`SimulatedGeneric` now fully wired, not just a skeleton**: v0.7.1 introduced `GenericDriver` (`drivers/generic.py`) and `SimulatedGeneric` (`drivers/simulated.py`) registered under `"GENERIC"`, but the factory routing still needed to prefer them. That wiring is now complete.
- **Issue #143 — unrecognized IDN no longer receives the wrong brand driver**: When an instrument's `*IDN?` doesn't match a known brand, `get_instrument()` previously grabbed the first registered driver for the requested type regardless of brand (e.g. a non-Keithley DMM could get Keithley-specific SCPI). It now falls back to `GenericDriver` unless exactly one unambiguous driver is registered for that type (e.g. a single plugin driver), and logs a warning when it does.
- **Issue #144 — `connect_instrument()` no longer hardcodes DMM as its fallback**: Unrecognized instruments (scopes, PSUs, signal generators, etc.) previously all fell through to a DMM driver. The fallback now routes to `"GENERIC"`, and ANRITSU/PROLOGIX IDN detection was added alongside the existing brand checks.
- **Issue #147 — SIM-mode `GENERIC` no longer secretly a multimeter**: `driver_type="GENERIC"` in simulation mode now returns `SimulatedGeneric` instead of `SimulatedMultimeter`.

### Tests
- New `tests/test_factory_routing.py`: mocked-VISA coverage for unrecognized-IDN routing, ambiguous-brand fallback, known-brand routing, SIM-mode GENERIC, and the ASRL/TDK-Lambda smart probe on unrelated serial devices (Issue #145).
- New regression suites this cycle: `tests/test_pxa.py` (83 tests), plus `test_async_wrapper_validation.py`, `test_check_errors.py`, `test_config.py`, `test_no_driver_consistency.py`, `test_serial_probe_filter.py`, `test_unsupported_feature.py`, and expanded `test_scanner.py`, `test_station.py`, `test_broadcaster.py`, `test_transport_utils.py`, `test_keithley.py`, `test_keysight.py`.
- **496 tests passing** (up from 458 at the start of the v0.8.0 hardening cycle).

## Key Features in v0.7.1

### Async & Batch Improvements
- **Issue #123 — async variant of `poll_for_mav`**: New `poll_for_mav_async()` in `transport.py` mirrors `poll_for_mav()` but uses `asyncio.sleep()` instead of blocking `time.sleep()`, so it can be awaited from async drivers/tests without stalling the event loop. The sync version is unchanged.
- **Issue #124 — `batch_query()` supports write-then-read**: `batch_query()` now accepts an optional `write_then_read` list of `(write_cmd, read_cmd)` pairs for instruments that need a separate write before the read (e.g. writing a register address, then reading its value). Results are keyed by `write_cmd`; existing `queries`-only calls are unaffected.

### CI
- **Issue #125 — Python 3.13 added to the test matrix**: CI now runs on 3.9–3.13. `requires-python` already covered this range.

### Generic Driver Skeleton (Issue #142, in progress)
- Added `GenericDriver` (`drivers/generic.py`) and `SimulatedGeneric` (`drivers/simulated.py`), both registered under the `"GENERIC"` driver type — a first-class fallback for unrecognized instruments instead of silently reusing brand-specific drivers. This is a skeleton: `factory.py`'s IDN-routing fallback and `connect_instrument()`'s hardcoded `"DMM"` fallback still need to be wired to prefer `GENERIC` (tracked separately in #143/#144).

### Packaging
- **`py.typed` marker added**: The package now ships a PEP 561 `py.typed` marker, so type checkers and editor IntelliSense pick up the existing type hints/docstrings from a `pip install` instead of treating the package as untyped.

### Tests
- 12 new tests (async `poll_for_mav`, `batch_query` write-then-read, GenericDriver registration/behavior).
- 365 total tests passing.

## Key Features in v0.7.0

### Windows Compatibility (Issue #143)
- **`get_rm()` no longer passes `None` to PyVISA**: On machines without the macOS NI-VISA framework (i.e. Windows), the shared resource manager is now created with an empty string so PyVISA auto-selects the available backend (system VISA if installed, otherwise the bundled `pyvisa-py`). Previously this crashed newer PyVISA versions with `AttributeError: 'NoneType' object has no attribute 'rsplit'` on every connection attempt.
- **PyInstaller packaging guide**: Documented how to build a single-file `.exe` — dynamically loaded modules (`pyvisa_py` and `instrumation.drivers.*`) are missed by static analysis, so they must be included explicitly with `--collect-all pyvisa_py` / `--collect-all instrumation` (see README and installation docs).

### Bug Fixes
- **Issue #135 — manual connections now update the VISA cache**: `get_instrument()` previously imported `json` inside the `AUTO` branch, making it a cell variable that was never bound on the manual-connection path. The cache-update block silently failed with `UnboundLocalError`. `json` is now a module-level import and the cache file is correctly written after successful manual connections.
- **Issue #131 — `connect_instrument()` propagates `ConfigurationError`**: Auto-detection no longer silently swallows this actionable error. `ConfigurationError` re-raises to the caller, while ordinary VISA/serial errors are still handled gracefully and logged.
- **Issue #132 — async context manager no longer leaks connections**: `AsyncInstrumentDriver.__aexit__()` now always calls `disconnect()` in a `finally` block, even when `shutdown_safety()` raises a `KeyboardInterrupt` (a `BaseException` the old `except Exception` missed). Both cleanup steps are bounded by a timeout so a hung driver cannot block exit.

### CI & Linting
- **Replaced flake8 with ruff** (Issue #126): CI now runs `ruff check .` across the whole repo. Ruff is scoped to the same hard-fail set flake8 enforced (`E9`/`F63`/`F7`/`F82` — syntax errors and undefined names), so the pre-existing style debt stays non-blocking.

### Community Contributions
- **@exharmonic** — PR #141: Added type hints to `utils.py`, `scanner.py`, and `transport.py` (Issue #128).
- **@webbrain-one** — PR #139: Replaced flake8 with ruff in CI (Issue #126).

### Tests
- 7 new regression tests covering the manual-connection cache fix, `ConfigurationError` propagation, and async cleanup on interrupt/timeout.
- 353 total tests passing.

## Key Features in v0.6.0

### New Feature: batch_query (Issue #119)
- **Efficient multi-query utility**: New `batch_query()` function sends multiple SCPI queries to an instrument in a single call and returns a dictionary mapping each query to its response.
- **Graceful error handling**: By default, failed queries are logged as error messages and processing continues. Use `stop_on_error=True` to raise on first failure.
- **Whitespace stripping**: Responses are automatically stripped for clean downstream parsing.
- **Example**:
  ```python
  from instrumation.transport import batch_query
  results = batch_query(dmm, ["*IDN?", "MEAS:VOLT:DC?", "*STB?"])
  for cmd, resp in results.items():
      print(f"{cmd} -> {resp}")
  ```

### Transport Utilities (Issues #113–#116)
- **`detect_line_termination()`**: Auto-detects the correct line termination character (LF, CR, or CRLF) for an instrument by trying each against a safe SCPI query.
- **`find_minimum_timeout()`**: Finds the smallest safe timeout value for an instrument by testing ascending candidates.
- **`poll_for_mav()`**: Polls the Status Byte Register for the MAV (Message Available) bit before reading, ensuring data is ready.
- **`poll_opc_with_backoff()`**: Polls for operation-complete with exponential backoff to reduce bus traffic during long operations.

### Scanner Utilities (Issue #117)
- **`find_duplicate_addresses()`**: Detects bus conflicts by identifying addresses that appear multiple times in a scan result with differing descriptions.

### Documentation
- New `docs/user_guide/transport_utils.md` — comprehensive guide for all transport and scanner utilities
- Updated API reference to include all new functions

### Tests
- 27 unit tests for transport utilities (up from 15)
- 5 regression tests for batch_query
- 90 tests passing in the transport/scanner-utilities module (full suite: 242, unchanged from v0.5.0)

### Other
- Version bumped to 0.6.0
- Added ROADMAP.md for v0.7.0 planning

## Key Features in v0.5.0

### Type Hints (Issue #108)
- **Complete type annotations across all driver files**: Added return type annotations and parameter type hints to every method in `base.py` and all 14 driver modules (`anritsu.py`, `keithley.py`, `keysight.py`, `prologix.py`, `real.py`, `registry.py`, `replay.py`, `rigol.py`, `rs.py`, `siglent.py`, `simulated.py`, `tdk.py`, `tektronix.py`).
- **500+ methods annotated**: Covers `InstrumentDriver`, `Multimeter`, `PowerSupply`, `SpectrumAnalyzer`, `NetworkAnalyzer`, `Oscilloscope`, `SignalGenerator`, `FunctionGenerator`, `ElectronicLoad`, and `FrequencyCounter` base classes plus all concrete implementations.
- **Benefits**: Full IDE autocomplete, mypy compatibility, and self-documenting API.

### Async / Await Support (Issue #107)
- **`AsyncInstrumentDriver`** and type-specific wrappers (`AsyncMultimeter`, `AsyncPowerSupply`, `AsyncSpectrumAnalyzer`, `AsyncNetworkAnalyzer`, `AsyncOscilloscope`, `AsyncSignalGenerator`, `AsyncFunctionGenerator`, `AsyncElectronicLoad`, `AsyncFrequencyCounter`): Explicit async versions of all instrument methods using `asyncio.to_thread`.
- **`wrap_async(driver)` factory**: Automatically picks the most specific async wrapper based on the driver's type hierarchy.
- **`async with` context manager**: `AsyncInstrumentDriver` supports async context management for clean connect/disconnect.
- **Parallel measurements**: Run measurements across multiple instruments concurrently with `asyncio.gather()` for faster test execution.
- **Backward compatible**: The existing `driver.async_*()` dynamic wrapper via `__getattr__` continues to work.

### Regression Test Suite
- **`tests/test_regression.py`**: 43 regression tests covering driver basics, MeasurementResult contract, safety guardrails, simulated physics, type hint completeness, async wrapper behavior, factory correctness, and registry integrity.
- **242 total tests** (up from 199 in v0.4.2), all passing.

## Key Features in v0.4.1

### Unit Tests: Rohde & Schwarz Drivers
- **`tests/test_rs.py`** ([#94](https://github.com/abduznik/instrumation/issues/94)): 21 new unit tests covering `RohdeSchwarzSG` (preset, frequency, amplitude, output, modulation states AM/FM/PULSE, start sweep, list sweep) and `RohdeSchwarzSA` (preset, center freq, span, RBW, VBW, peak search, marker amplitude, trace data binary format).

### Unit Tests: Prologix GPIB-USB Bridge
- **`tests/test_prologix.py`** ([#93](https://github.com/abduznik/instrumation/issues/93)): 11 new unit tests covering `PrologixDriver` bridge initialization sequence (++mode, ++auto, ++eoi, ++addr), GPIB address switching, query read-eoi protocol, and the `write()` newline-append rules for SCPI vs Prologix `++` commands.

### Multi-Python CI Matrix
- **`.github/workflows/main.yml`** ([#97](https://github.com/abduznik/instrumation/issues/97)): CI now tests against Python `3.9`, `3.10`, `3.11`, and `3.12` in parallel via `strategy.matrix`. Previously only `3.10` was tested.

### Test Count
188 tests passing (up from 156 in v0.4.0).

## Key Features in v0.4.0

### Oscilloscope Channel-Aware Measurements
- **Formalized channel-aware API** ([#87](https://github.com/abduznik/instrumation/issues/87)): Oscilloscope base class now declares channel-aware abstract methods `measure_frequency(channel=1)`, `measure_duty_cycle(channel=1)`, and `measure_v_peak_to_peak(channel=1)`. All scope drivers (KeysightInfiniiVision, SiglentSDS, TektronixTDS, SimulatedOscilloscope, ReplayDriver) updated accordingly.

### Simulated Driver Completeness
- **SimulatedPowerSupply print stubs** ([#82](https://github.com/abduznik/instrumation/issues/82)): `set_ovp`, `set_ocp`, and `clear_protection` now log their actions.
- **SimulatedPowerSupply realistic power** ([#83](https://github.com/abduznik/instrumation/issues/83)): `measure_power()` now returns `voltage * 0.5` instead of hardcoded 0.0W.
- **SimulatedOscilloscope set_trigger** ([#84](https://github.com/abduznik/instrumation/issues/84)): Trigger configuration now prints source, level, and slope parameters.
- **SimulatedNetworkAnalyzer marker stubs** ([#85](https://github.com/abduznik/instrumation/issues/85)): `peak_search`, `get_marker_x`, and `get_marker_y` now log marker index.

### Frequency Counter Driver
- **Already implemented**: FrequencyCounter base class, Keysight53230A real driver, and SimulatedFrequencyCounter with full test coverage (11 tests) — tracked and closed as completed.

### Maintenance
- **Root directory cleanup**: Removed tracked artifacts (experiment images, session files, MkDocs build output, macOS .DS_Store) and added comprehensive .gitignore patterns.
- **Gemini workflows removed**: All 6 gemini GitHub Actions workflow files deleted.

## Key Features in v0.3.2

### Simulated Driver Completeness
- **SimulatedMultimeter enhancements**: Added `measure_temperature()` ([#68](https://github.com/abduznik/instrumation/issues/68)), `measure_capacitance()` and `measure_diode()` ([#69](https://github.com/abduznik/instrumation/issues/69)), and `measure_period()` ([#70](https://github.com/abduznik/instrumation/issues/70)) — achieving parity with `SimulatedKeysight34461A`.
- **SimulatedOscilloscope print stubs** ([#71](https://github.com/abduznik/instrumation/issues/71)): `run()`, `stop()`, `single()`, and `auto_scale()` now log their actions instead of being silent `pass` stubs.
- **SimulatedSpectrumAnalyzer RBW/VBW** ([#72](https://github.com/abduznik/instrumation/issues/72)): `set_rbw()` and `set_vbw()` now store the value and print a simulation log.
- **SimulatedSignalGenerator set_output** ([#75](https://github.com/abduznik/instrumation/issues/75)): `set_output()` now prints the ON/OFF state.
- **shutdown_safety update** ([#78](https://github.com/abduznik/instrumation/issues/78)): Improved safety protocol across simulated drivers.
- **Electronic Load noise fix**: Suppressed noise in `SimulatedElectronicLoad.measure_voltage()` when input is off.

### Exports & DX
- **driver classes exported** ([#73](https://github.com/abduznik/instrumation/issues/73)): All key simulated driver classes (`SimulatedMultimeter`, `SimulatedPowerSupply`, `SimulatedSpectrumAnalyzer`, `SimulatedNetworkAnalyzer`, `SimulatedOscilloscope`, `SimulatedSignalGenerator`, `SimulatedKeithley2400`, `SimulatedKeysight34461A`, `SimulatedElectronicLoad`) now directly importable from `instrumation.drivers`.

## Key Features in v0.3.1

### New Instrument Drivers
- **DC Electronic Load**: Full digital twin simulation for programmable DC electronic loads with Constant Current (CC), Constant Voltage (CV), Constant Resistance (CR), and Constant Power (CP) modes. Includes physics-based power dissipation modeling, OVP/OCP/OPP protection simulation, and foldback mode support. Registered as `"E_LOAD"` type.
- **Siglent SDL1000X Load Driver**: Real hardware driver for Siglent SDL1000X series programmable DC electronic loads, with full CC/CV/CR/CP mode support.

### Community Contributions
- **@AYUSH4951 (Ayush Sharma)** — [#67](https://github.com/abduznik/instrumation/pull/67): Fixed `ReplayDriver.measure_voltage_actual()` returning hardcoded `0.0 V` instead of delegating to the replay log. Now correctly reads recorded responses from golden master files.
- **@Sula-bh (Sulabh Acharya)** — [#66](https://github.com/abduznik/instrumation/pull/66): Added type hints to `SimulatedPowerSupply` methods for better IDE support and static analysis.
- **@krishna7805 (Mohan R. Barde)** — [#65](https://github.com/abduznik/instrumation/pull/65): Replaced stale BUG-related comments in adversarial tests with regression-guard terminology to avoid misleading references to already-fixed behavior.

### Digital Twin Improvements
- **SimulatedKeithley2400.configure_voltage_ac()**: AC voltage configuration now prints a warning (matching real hardware — 2400 doesn't support AC) and falls back to DC voltage mode.
- **SimulatedSpectrumAnalyzer.peak_search()**: Full peak-search implementation that generates realistic sweep data across the configured frequency span, finds the highest-amplitude signal. `get_trace_data()` now returns actual generated data instead of zeros.
- **AFG-DSOX loopback fix**: Square wave output corrected in the AFG-DSOX loopback digital twin experiment.

### Exports & DX
- `ReplayDriver` is now directly importable as `from instrumation.drivers import ReplayDriver`.
- `search_devices` added to `__all__` in `src/instrumation/__init__.py`.

### CI & Infrastructure
- Removed stale Gemini workflow.
- Fixed `test_broadcaster.yml` to install `pytest-asyncio`.
- Bumped all CI actions to Node.js 24-compatible versions.
- Added cache-busting hash to docs image URL for reliable image rendering.

## Key Features in v0.3.0

### New Instrument Drivers
- **Keithley 2400 SourceMeter (SMU)**: Full dual-role driver registered as both `DMM` and `PSU`. Source voltage/current, set compliance limits, OVP/OCP protection, output control, and measure voltage/current/resistance/power — all through one unified SMU interface.
- **Keysight 34461A Truevolt DMM**: 6.5-digit precision multimeter with DCV, ACV, DCI, ACI, 2-wire/4-wire resistance, frequency, period, temperature (thermocouple/RTD), capacitance, and diode test measurements.
- **Digital Twin parity**: Both new instruments have fully simulated counterparts (`SimulatedKeithley2400`, `SimulatedKeysight34461A`) with state tracking for offline development.

### Bug Fixes
- **MeasurementResult.**__format__** fixed**: `f"{result:.2f}"` no longer crashes with `ValueError` when the value is a list or `None`.
- **SimulatedPowerSupply state tracking**: `get_voltage()` now returns the value set by `set_voltage()`, and `get_output()` reflects `set_output()` — the simulation actually tracks state now.
- **`is_sim_mode()` consistency**: `factory.is_sim_mode()` now recognizes both `"SIM"` and `"SIMULATED"` environment values, matching `config.is_sim_mode()`.

### Testing Infrastructure
- **Adversarial test suite**: 27 new edge-case tests added as permanent regression coverage (`tests/test_adversarial.py`), catching format crashes, state leaks, and interface inconsistencies.
- Total test coverage: **126 tests** (up from 73), all passing with zero regressions.

## Key Features in v0.2.0

### Advanced Hardware Integration
- Keysight PXA N9030A Support: Fully validated integration with high-speed 32-bit binary trace transfers and Little-Endian byte-swapping logic.
- Signal Generator Enhancements: New support for Frequency/Power sweeps and Modulation state control (AM/FM/Pulse) for Keysight MXG/EXG series.

### Digital Twin & Simulation
- Golden Master Engine: New `RecordingWrapper` and `ReplayDriver` allow you to record real hardware sessions and replay them as bit-perfect simulations for offline testing.
- Replay Protocol: Connect using `replay://path/to/session.json` to simulate any supported instrument type.

### Intelligent Discovery
- Enhanced AUTO Address: New priority engine automatically finds instruments over HiSLIP/TCPIP first, followed by USB and GPIB, while filtering out system serial ports.
- Low-Level Scanner: Improved mDNS and ARP scanning for finding instruments on complex networks.

### Visualization & DX
- Spectrum Plotting: Built-in Matplotlib support for generating professional-grade spectrum plots from live or replayed trace data.
- 100% Stability: Full unit test coverage for all Spectrum Analyzer drivers (Rigol, R&S, Anritsu, Keysight).
