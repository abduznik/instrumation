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
