# Log: Keeping it Real (Async & Latency Fixes)
**Commit**: `0148197`

## Overview
Fixed those annoying async test failures. The Digital Twin was being "too fast" which broke our timing assertions. If a DMM returns in 0.001s, we can't really test if parallel execution is working as expected.

## Technical Lowdown
- **Testing**: Fixed `TypeError` in `test_async.py` by correctly using `async_` prefixes for synchronous driver methods.
- **Simulation**: Added `time.sleep(self.latency)` to all measurement methods in the simulated base driver.
- **API Cleanup**: Synchronized test assertions with the finalized `get_marker_amplitude()` naming convention.

## Why it matters
Asynchronous tests were failing because the simulation was too efficient. Adding simulated latency lets us verify that our `asyncio.gather` calls actually run in parallel as intended.
