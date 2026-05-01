# Log: Context is Everything (Test Bench Modernization)
**Commit**: `e546b3a`

## Overview
Modernized the production test bench example to be more "set it and forget it". The biggest win here was adding proper context manager support for UUT handling.

## Technical Lowdown
- **UUTHandler**: Added `__enter__` and `__exit__` to `UUTHandler`. Now it automatically closes serial/VISA sessions even if your test crashes.
- **Logic**: Updated the pass/fail logic in the example to use the standardized `MeasurementResult` objects.
- **Robustness**: Improved error catching for serial connections that don't exist on all machines.

## Why it matters
Leaving serial ports open in a hung state is the #1 cause of "why is the lab PC frozen?" calls. Proper resource management in the test bench script keeps the hardware happy.
