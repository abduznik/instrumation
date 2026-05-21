# Log: Keithley 2400 SourceMeter (SMU) Driver
**Commits**: `e50027c`

## Overview
The Keithley 2400 had a bare-bones stub that only overrode `measure_resistance()`. We turned it into a full Source Measure Unit implementing both the `PowerSupply` and `Multimeter` interfaces simultaneously.

## Technical Lowdown
- **Dual registration**: `@register_driver("DMM")` and `@register_driver("PSU")` so the factory can find it as either type.
- **Source side**: `set_voltage()`, `get_voltage()`, `set_current()` (source mode), `set_current_limit()` (compliance), `set_output()`, `get_output()`, `set_ovp()`, `set_ocp()`, `clear_protection()`, `measure_power()`.
- **Measure side**: Full Multimeter compliance — DCV, DCI, 2W/4W resistance, frequency, auto-range.
- **Safety**: `shutdown_safety()` kills output, zeros both source voltage and current.
- **Digital Twin**: `SimulatedKeithley2400` tracks all state (voltage, current, output, source mode) so you can develop SMU sequences offline.

## Why it matters
The 2400 is the workhorse of every semiconductor test bench. Having a proper SMU driver with digital twin parity means you can write and debug component characterisation scripts without tying up the lab instrument.
