# Log: v0.3.1 — Digital Twin Completeness
**Commits**: `286279d`, `436a3a9`, `c25bf4b`, `7789bf2`, `7e4903e`, `6a56e09`, `6a9f55f`, `6231af0`, `e69cecb`, `0fcace4`, `e25fc19`

## Overview
A packed release with the new DC Electronic Load driver (physical + digital twin), 3 community PRs, and rounding out the remaining Digital Twin method stubs.

## New Drivers

### DC Electronic Load (`6a56e09`)
Added a full programmable DC electronic load driver with physics-based digital twin simulation:
- **4 operating modes**: Constant Current (CC), Constant Voltage (CV), Constant Resistance (CR), Constant Power (CP)
- **Physics engine**: Real-time power dissipation calculation with configurable source voltage (Vs = 12V) and series resistance (Rs = 0.05&Omega;)
- **Protection simulation**: OVP, OCP, OPP thresholds with automatic input shutdown
- **Foldback modes**: Current foldback and power foldback with configurable delay and auto-start
- **Siglent SDL1000X driver**: Real hardware driver registered as `"E_LOAD"` with full mode support

## Community Contributions

### @AYUSH4951 — ReplayDriver voltage fix (#67, `7e4903e`)
`ReplayDriver.measure_voltage_actual()` was returning hardcoded `0.0 V`, completely bypassing the golden master replay log. Fixed by delegating to `self.measure_voltage()` which correctly reads recorded responses.

### @Sula-bh — Type hints for SimulatedPowerSupply (#66, `7789bf2`)
Added parameter and return type annotations to all `SimulatedPowerSupply` methods for better IDE support.

### @krishna7805 — Clean up stale bug comments (#65, `c25bf4b`)
Replaced outdated `BUG` wording in adversarial test comments with regression-guard terminology, making it clear these are permanent guards rather than references to unfixed bugs.

## Digital Twin Improvements

### SimulatedKeithley2400.configure_voltage_ac() (`e69cecb`)
The 2400 SourceMeter doesn't support true AC voltage measurement (real hardware falls back to DC mode). The simulated twin now prints a warning and sets source mode to VOLT, matching hardware behavior instead of silently passing.

### SimulatedSpectrumAnalyzer.peak_search() (`0fcace4`)
Added sweep data generation with configurable center frequency and span, seeded with a random peak signal above a noise floor. `peak_search()` finds the actual highest-amplitude point in the sweep data. `get_trace_data()` now returns real generated data instead of a flat zero array.

### AFG-DSOX Loopback Fix (`6a9f55f`)
Corrected the square wave output in the AFG-DSOX loopback digital twin experiment and regenerated the experiment image for accurate documentation.

### Missing Exports (`e25fc19`)
- `ReplayDriver` is now importable as `from instrumation.drivers import ReplayDriver`
- `search_devices` added to `__all__` in `src/instrumation/__init__.py`

## CI & Infrastructure
- Removed stale Gemini workflow (`436a3a9`)
- Fixed `test_broadcaster.yml` to install `pytest-asyncio` (`436a3a9`)
- Bumped all CI actions to Node.js 24-compatible versions (`286279d`)
- Added cache-busting hash to docs image URL (`6231af0`)

## Stats
- **138 tests** passing (up from 126)
- **3 community contributors** — @AYUSH4951, @Sula-bh, @krishna7805
- **12 commits** since v0.3.0
