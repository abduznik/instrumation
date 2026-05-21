# Log: Bug Bash & Adversarial Testing
**Commits**: `9b563c4`, `ade9056`, `bd4e5bc`, `1494700`

## Overview
Spent the session stress-testing the HAL from every angle — found 4 real bugs, fixed them all, and built a permanent adversarial regression suite to keep them from coming back.

## Bugs Found & Fixed

### 1. `MeasurementResult.__format__` Crash (Medium)
`f"{result:.2f}"` on a list-valued or `None` result hit `format(str(...), format_spec)` which raises `ValueError: Unknown format code 'f' for object of type 'str'`. The fix: return `str(self.value)` unconditionally when the value isn't a scalar — no format code to complain about.

### 2. Simulated PSU State Tracking (High)
`SimulatedPowerSupply` was a ghost town — `set_voltage(5.0)` printed the intent but `get_voltage()` handed back `0.0` every time. Same for `set_output(True)` / `get_output()`. Both now store their setpoints in instance variables.

### 3. `is_sim_mode()` Inconsistency (Medium)
`factory.is_sim_mode()` only checked for `"SIM"` while `config.is_sim_mode()` also supported `"SIMULATED"`. Anyone setting `INSTRUMATION_MODE=SIMULATED` would silently get real hardware mode from the factory path. Factory now matches config.

## Attack Surface
27 adversarial tests now probe edge cases:
- MeasurementResult dunders with invalid types (lists, None, complex)
- PSU state leakage between operations
- Safety guardrail boundary conditions (negative frequency, over-power)
- Factory AUTO with zero hardware available
- `is_sim_mode()` env value consistency
- Async method dispatch on non-existent methods
- Repeated connect/disconnect cycling
- Instrument isolation (shared state check)
