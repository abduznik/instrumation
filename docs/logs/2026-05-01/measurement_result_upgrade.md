# Log: Data with Style (MeasurementResult Upgrades)
**Commit**: `36fb041`

## Overview
Beefed up the `MeasurementResult` class to make it the central source of truth for all data leaving the drivers. No more raw lists floating around.

## Technical Lowdown
- **Collections**: Added support for handling collections of results (like traces) while keeping the same easy-to-use API.
- **Compatibility**: Added `__iter__` and `__getitem__` so it behaves like a list when needed, keeping old scripts from breaking.
- **Formatting**: Implemented a `format()` method that handles SI unit conversion and decimal precision automatically.

## Why it matters
By standardizing the output format early, we made it possible to add high-speed binary traces and VNA complex data without having to rewrite every example script's print statements.
