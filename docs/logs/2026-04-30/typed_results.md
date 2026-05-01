# Log: Typed Results & Driver Registration
**Commit**: `44c20d8`, `9ac5c43`

## Overview
Massive refactor to how drivers return data. We moved away from raw numbers and strings toward a unified, typed measurement system.

## Technical Lowdown
- **MeasurementResult**: Standardized all measurement returns to use the `MeasurementResult` object, which bundles the value with its SI unit.
- **Registration**: Implemented a `@register_driver` decorator to handle how the factory discovers and instantiates different instrument brands.
- **Factory**: Consolidated multiple factory systems into a single, robust entry point.

## Why it matters
This refactor removed a lot of "guesswork" from the codebase. When you call a measure function, you now get an object that knows its unit and how to format itself, which prevents unit-conversion bugs in analysis.
