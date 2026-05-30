# Log: v0.4.0 — Simulated Driver Polish & Scope API Standardization
**Commits**: `1350cb4`, `7ccfed6`, `e45775c`, `d7777cb`, `7ebfbdc`, `0e70c48`

## Overview
A focused quality-of-life release rounding out simulated driver method stubs, formalizing the oscilloscope channel-aware measurement API, and cleaning up repository artifacts.

## Simulated Driver Polish

### SimulatedPowerSupply
- **OVP/OCP/Protection stubs** (`1350cb4`): `set_ovp`, `set_ocp`, and `clear_protection` now print `[SIM]` log messages consistent with other methods in the class.
- **Realistic power calculation** (`7ccfed6`): `measure_power()` now computes `voltage * 0.5` instead of returning hardcoded `0.0W`. Uses `getattr` with default to handle calls before `set_voltage`.

### SimulatedOscilloscope
- **set_trigger stub** (`e45775c`): Trigger configuration now prints source, level, and slope parameters.

### SimulatedNetworkAnalyzer
- **Marker stubs** (`d7777cb`): `peak_search`, `get_marker_x`, and `get_marker_y` now log the marker index being queried.

## Oscilloscope Channel-Aware API

### Base class formalization (`7ebfbdc`)
The `Oscilloscope` abstract base class now declares `measure_frequency(channel=1)`, `measure_duty_cycle(channel=1)`, and `measure_v_peak_to_peak(channel=1)` as abstract methods. These were already implemented ad-hoc by `KeysightInfiniiVision`, `SiglentSDS`, and `TektronixTDS` — the change simply formalizes the contract.

### SimulatedOscilloscope & ReplayDriver
Both updated with channel-aware overrides that accept the `channel` parameter and pass it through to existing measurement logic.

## Repository Hygiene

### Artifact cleanup (`0e70c48`)
- Removed 10 tracked files from root: experiment screenshots, VISA cache, session JSON blobs, MkDocs site build output (58 files), usage guide, test CSV output
- Added comprehensive `.gitignore` covering build artifacts, OS files, runtime caches, and experiment outputs

### Gemini workflows removed (`caa4160`)
All 6 gemini GitHub Actions workflow files deleted from `.github/workflows/`.
