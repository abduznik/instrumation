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
