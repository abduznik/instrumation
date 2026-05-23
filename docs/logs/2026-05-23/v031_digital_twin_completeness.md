# Log: v0.3.1 — Digital Twin Completeness
**Commits**: `e69cecb`, `0fcace4`, `e25fc19`

## Overview
Closed all 3 open good-first-issues to round out Digital Twin method coverage. Every simulated instrument method now has a real implementation — no more `pass` stubs for documented features.

## Changes

### SimulatedKeithley2400.configure_voltage_ac() (`e69cecb`)
The 2400 SourceMeter doesn't support true AC voltage measurement (real hardware falls back to DC mode). The simulated twin now prints a warning and sets source mode to VOLT, matching hardware behavior instead of silently passing.

### SimulatedSpectrumAnalyzer.peak_search() (`0fcace4`)
Added sweep data generation with configurable center frequency and span, seeded with a random peak signal above a noise floor. `peak_search()` finds the actual highest-amplitude point in the sweep data. `get_trace_data()` now returns real generated data instead of a flat zero array.

### Missing Exports (`e25fc19`)
- `ReplayDriver` is now importable as `from instrumation.drivers import ReplayDriver`
- `search_devices` added to `__all__` in `src/instrumation/__init__.py`

## Stats
- **138 tests** passing (up from 126)
