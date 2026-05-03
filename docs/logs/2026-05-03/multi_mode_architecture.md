# Dev Log: Multi-Mode Architecture & Specialized VNA Support (2026-05-03)

As we moved into high-end laboratory validation, we encountered a new class of "Combo" instruments (like Keysight FieldFox and Anritsu VNA Master) that break the traditional one-instrument-per-driver model.

## Architectural Shift: The "Combo" Pattern

### The Problem
Traditional SCPI drivers assume a static mode (e.g., a Spectrum Analyzer stays a Spectrum Analyzer). Instruments like the FieldFox change their entire command tree when switching from SA to NA mode.

### The Solution: Option A (Pragmatic Multi-Inheritance)
We implemented a mode-aware driver pattern. A single class now inherits from multiple base interfaces (e.g., `SpectrumAnalyzer` and `NetworkAnalyzer`).
- **Internal State Management**: Every high-level method call now triggers an internal `_set_mode()` check.
- **Lazy Switching**: If the instrument is already in the correct mode, no command is sent, preserving performance.

## Specialized Driver Implementations

### Anritsu ShockLine (MS46522B/MS46524B)
- **Problem**: These VNAs use a unique namespaced SCPI tree (`:SENSe1:`) that generic drivers ignore.
- **Fix**: Created `AnritsuShockLineVNA` with full support for channel-based measurement selection and 32-bit binary trace fetching.

### Keysight FieldFox & Anritsu VNA Master
- **Problem**: Handheld combo units requiring mode selection via `:INSTrument:SELect`.
- **Fix**: Implemented `KeysightFieldFox` and `AnritsuMS2035B` drivers. They seamlessly transition between SA and NA modes depending on the method called.

## Factory Evolution: Smart Routing
The factory was upgraded from simple brand-matching to deep `*IDN?` inspection.
- **Probing**: The factory now performs a "pre-flight" IDN query to detect specific model numbers.
- **Routing**: It routes handheld combo units to the specialized `COMBO_VNA_SA` drivers, while keeping benchtop VNAs on the high-performance `NA` drivers.

**Impact**: This shift prepares the HAL for "Swiss Army Knife" instruments common in field engineering, ensuring the user API remains simple while the backend handles the complexity of state management.
