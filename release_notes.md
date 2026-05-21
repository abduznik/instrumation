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
