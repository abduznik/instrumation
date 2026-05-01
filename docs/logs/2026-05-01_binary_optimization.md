# Log: Turbo-charging Traces (Binary REAL)
**Commit**: `95ccc87`

## Overview
Parsing 10,001 floats from an ASCII string is just... painful. It's slow, it's CPU-intensive, and it feels like 1995. We finally moved all major drivers (Keysight, R&S, Anritsu, Rigol) to native binary REAL data transfer.

## Technical Lowdown
- **PyVISA Magic**: We're now using `query_binary_values()` instead of `query_ascii()`.
- **Command Overhaul**: Standardized commands like `:FORM REAL,32` and `:FORM:TRAC:DATA REAL` across different brands.
- **Speed Win**: Data hits your Python script as a ready-to-go list/numpy array without the "comma-split-float-convert" dance.

## Why it matters
In high-throughput ATE, every millisecond counts. Moving to binary is the single biggest performance win for SA and VNA trace extraction we've had yet.
