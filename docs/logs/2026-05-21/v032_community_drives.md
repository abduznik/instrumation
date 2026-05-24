# Log: v0.3.2 — Community-Driven Digital Twin Completeness
**Commits**: `5fec6e3`, `1406a64`

## Overview
A focused release rounding out the remaining Digital Twin method stubs — 5 issues fixed in a single session, plus a CD pipeline push to PyPI. All changes driven by the open issue tracker and community-friendly good-first-issue format.

## Digital Twin Method Stubs

### SimulatedMultimeter.measure_period() ([#70](https://github.com/abduznik/instrumation/issues/70))
Added `measure_period()` returning `MeasurementResult(0.001, "s")`, matching the implementation already present in `SimulatedKeysight34461A`.

### SimulatedOscilloscope Run/Stop/Single/Auto-Scale ([#71](https://github.com/abduznik/instrumation/issues/71))
Replaced silent `pass` stubs for `run()`, `stop()`, `single()`, and `auto_scale()` with `print()` calls that log the action (e.g. `[SIM] Scope: Run`), matching the pattern of other simulated methods.

### SimulatedSpectrumAnalyzer RBW/VBW ([#72](https://github.com/abduznik/instrumation/issues/72))
`set_rbw()` and `set_vbw()` now store the value to `self._rbw`/`self._vbw` and print a simulation log. Defaults initialized to `1e3` in the constructor.

### SimulatedSignalGenerator set_output() ([#75](https://github.com/abduznik/instrumation/issues/75))
Changed `set_output()` from a silent `pass` stub to a print stub that logs `[SIM] SG Output: ON/OFF`.

### Driver Module Exports ([#73](https://github.com/abduznik/instrumation/issues/73))
All key simulated driver classes (`SimulatedMultimeter`, `SimulatedPowerSupply`, `SimulatedSpectrumAnalyzer`, `SimulatedNetworkAnalyzer`, `SimulatedOscilloscope`, `SimulatedSignalGenerator`, `SimulatedKeithley2400`, `SimulatedKeysight34461A`, `SimulatedElectronicLoad`) are now directly importable from `instrumation.drivers`.

## Infrastructure

### Issues Created ([#79](https://github.com/abduznik/instrumation/issues/79) – [#87](https://github.com/abduznik/instrumation/issues/87))
9 new issues created for the community:
- **7 Good First Issues** (#79–#85): print stubs and small improvements across simulated drivers
- **2 Help Wanted Major Issues** (#86–#87): Frequency Counter driver and channel-aware scope measurements

### CD Pipeline
- Version bumped to **v0.3.2**
- GitHub Release [`v0.3.2`](https://github.com/abduznik/instrumation/releases/tag/v0.3.2) created, triggering automatic PyPI publish
- **140 tests** passing with zero regressions

## Stats
- **140 tests** passing (up from 138)
- **5 issues fixed** in one session
- **9 new issues** opened for community contribution
- **1 new contributor issue format** established (good-first-issue with code snippets)
