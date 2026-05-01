# Log: High-Speed Binary Trace Extraction
**Date**: 2026-05-01
**Commit**: `95ccc87`

## Overview
Optimized trace and waveform extraction by replacing ASCII string parsing with native REAL binary data transfer.

## Technical Changes
- **Core**: Added `query_binary_values()` to `InstrumentDriver` and implemented it in `RealDriver` via PyVISA.
- **Drivers**: Updated Keysight, R&S, Anritsu, and Rigol drivers to use binary modes (e.g., `:FORM REAL,32`).
- **Optimization**: Significant reduction in I/O overhead and CPU cycles for high-resolution traces (up to 10k points).
- **Verification**: Updated PNA unit tests to mock and verify binary command sequences.

## Why
ASCII parsing of 10,001 comma-separated floats is extremely slow and prone to buffer overflows on some interfaces. Binary transfer is the industry standard for production-grade ATE performance.
