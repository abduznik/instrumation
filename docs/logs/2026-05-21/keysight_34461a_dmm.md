# Log: Keysight 34461A Truevolt DMM Driver
**Commits**: `e50027c`

## Overview
Added a full-featured driver for the Keysight 34461A / 34460 series 6.5-digit multimeters — the modern successor to the legendary 34401A.

## Capabilities
- **DCV/ACV**: Auto or manual ranging, true-RMS AC
- **DCI/ACI**: Current measurements with shunt switching
- **Resistance**: 2-wire and 4-wire (offset-compensated)
- **Frequency / Period**: Audio-band through RF
- **Temperature**: Thermocouple (J, K, T, E, N, R, S) and RTD (PT100)
- **Capacitance**: 1 nF to 10 mF range
- **Diode test**: Forward voltage measurement
- **Factory routing**: Auto-detected when `*IDN?` contains `"34461"` or `"34460"`

## Digital Twin
`SimulatedKeysight34461A` produces realistic values (4.95 V DCV, 1000 Ohm resistance, 23.5C temperature) and supports all measurement functions so data pipeline development works offline.
