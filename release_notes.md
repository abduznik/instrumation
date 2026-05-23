## Key Features in v0.3.1

### New Digital Twin Features
- **SimulatedKeithley2400.configure_voltage_ac()**: Implemented AC voltage configuration with a warning that the 2400 does not support true AC voltage (matching real hardware behavior). Falls back to DC voltage mode.
- **SimulatedSpectrumAnalyzer.peak_search()**: Full peak-search implementation that generates realistic sweep data across the configured frequency span and finds the highest-amplitude signal. Also improves `get_trace_data()` to return actual generated data instead of zeros.
- **peaks on SimulatedSpectrumAnalyzer**: Sweep data is regenerated when center frequency or span changes, keeping simulations realistic.

### Exports & DX
- **ReplayDriver** is now directly importable as `from instrumation.drivers import ReplayDriver`.
- **search_devices** is now exportable as `from instrumation import search_devices` (added to `__all__`).

### Bug Fixes
- None — this release focuses on Digital Twin method completeness for easier offline development.

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
