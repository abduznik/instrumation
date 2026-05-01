# Log: Async Regressions & Latency Simulation
**Date**: 2026-05-01
**Commit**: `0148197`

## Overview
Resolved regressions in asynchronous measurement tests and improved the Digital Twin's timing accuracy.

## Technical Changes
- **Testing**: Fixed `TypeError` in `test_async.py` by correctly using `async_` prefixes for synchronous driver methods.
- **Simulation**: Added `time.sleep(self.latency)` to all measurement methods in `SimulatedBaseDriver`.
- **API Cleanup**: Synchronized test assertions with the finalized `get_marker_amplitude()` naming convention.

## Why
Asynchronous tests were failing because the Digital Twin was returning instantly, making parallel timing assertions invalid. Additionally, attempting to `await` synchronous methods caused runtime errors.
