# Roadmap — v0.9.0

**Target Release:** Q3 2026

---

## New Feature: Generic/Fallback Instrument Driver

Unrecognized instruments (unknown `*IDN?`) previously either silently received a brand-specific driver for their requested type (sending the wrong vendor's SCPI dialect) or, in the narrow real-hardware `driver_type="GENERIC"` path, an undocumented/unregistered `RealDriver`. `GenericDriver` (`drivers/real.py`) and `SimulatedGeneric` (`drivers/simulated.py`) are now first-class, registered (`@register_driver("GENERIC")`) drivers usable directly:

```python
from instrumation import get_instrument
dev = get_instrument("TCPIP::192.168.1.50::INSTR", "GENERIC")
dev.write("*RST")
print(dev.query("*IDN?"))
```

### What changed

- `factory.py`'s no-IDN-match fallback now only reuses a type-registered driver when there is exactly one unambiguous candidate (e.g. a single plugin driver); otherwise it uses `GenericDriver` and logs a warning instead of guessing a brand.
- `connect_instrument()` (`__init__.py`) no longer hardcodes `"DMM"` as its fallback — unrecognized instruments now route to `"GENERIC"`. ANRITSU and PROLOGIX IDN checks were added to its routing table.
- SIM-mode `driver_type="GENERIC"` now returns `SimulatedGeneric`, not `SimulatedMultimeter` (gh #147, verified: `test_sim_generic_is_not_multimeter`).
- Added mocked-VISA regression tests for IDN routing, the no-match fallback, and the ASRL/TDK-Lambda smart probe (`tests/test_factory_routing.py`).

### Why it matters

Sending a brand's vendor-specific SCPI commands to an instrument that never claimed to speak that dialect can produce wrong results or trigger hardware errors silently. Unrecognized instruments now get safe, generic SCPI access instead of a guessed brand driver.

---

## Planned: Live Instrument Dashboard

The dashboard (issues #118 launch, #119 React status cards, #120 CSV/JSON export) is **planned, not yet shipped** — tracked by the open enhancement issues. The current `DataBroadcaster` (UDP/JSON, `utils.py`) provides the streaming foundation, and `examples/common/broadcast_demo.py` shows a zero-dependency receiver. The `launch_dashboard()` module described below is the target design once #118–#120 are implemented.

### Target design

- Auto-discovers instruments and shows them in a clean table
- Streams live readings (voltage, current, frequency, etc.) to the browser in real-time
- Color-coded status indicators (connected, measuring, error, idle)
- Export readings to CSV/JSON with one click (#120)
- Works in SIM mode for demos and development

### Architecture (target)

```
┌─────────────┐      UDP/JSON       ┌─────────────────┐
│ Instrument  │ ──────────────────> │ Web Dashboard   │
│ (DataBroad.)│                     │ (browser/WS)    │
└─────────────┘                     └─────────────────┘
```

- `instrumation.dashboard` — New module (FastAPI-lite or plain websockets)
- Reuses existing `DataBroadcaster` for instrument-side streaming
- Single `launch_dashboard(port=8080)` call to start

---

## Bug Fixes & Improvements

All issue numbers below were reconciled against actual code + issue state (gh #158).

| Issue | Description | Priority |
| --- | --- | --- |
| #117 | Detect duplicate-address bus conflicts from scan results | ✅ Fixed |
| #121 | `find_duplicate_addresses` doesn't handle empty/`None` scan list | ✅ Fixed (`if not devices: return []` + tests for `[]`/`None`/same-desc-different-type) |
| #122 | `.visa_cache.json` not created on first run | ~~Low~~ ✅ Fixed in v0.6.0 |
| #123 | Add async variant of `poll_for_mav` | ✅ Fixed (`poll_for_mav_async` in `transport.py`) |
| #124 | Add `write_then_read` pattern to `batch_query` | ✅ Fixed (`batch_query(..., write_then_read=...)` in `transport.py`) |
| #125 | CI: Add Python 3.13 to test matrix | ✅ Fixed (`main.yml` matrix runs 3.9–3.13) |
| #126 | CI: Add ruff linting | ✅ Fixed (ruff check in `main.yml`) |
| #127 | Remove deprecated `UUTHandler` (device.py) | ✅ Fixed in v0.9.0 (`device.py` deleted; top-level `connect()` removed with it) |
| #128 | Add type hints to `utils`, `scanner`, `transport` | ✅ Fixed |
| #129 | Add NumPy-style docstrings to public API | ✅ Fixed |
| #130 | ReplayDriver: read values from golden master | ✅ Fixed (`replay://` resource scheme in `factory.py`) |
| #131 | `connect_instrument()` swallows `ConfigurationError` | ~~High~~ ✅ Fixed in v0.7.0 |
| #132 | Async wrapper leaks connections on `KeyboardInterrupt` | ~~High~~ ✅ Fixed in v0.7.0 |
| #135 | Manual-connection cache update fails with `UnboundLocalError` | ~~High~~ ✅ Fixed in v0.7.0 |
| #142 | Add a real `GenericDriver` fallback for unrecognized instruments | ~~High~~ ✅ Fixed in v0.8.0 |
| #143 | Unknown-IDN instrument could silently receive the wrong brand-specific driver | ~~High~~ ✅ Fixed in v0.8.0 |
| #144 | `connect_instrument()` hardcoded DMM as fallback for any unrecognized instrument | ~~High~~ ✅ Fixed in v0.8.0 |
| #145 | `factory.py`'s real-hardware IDN-routing and discovery paths were untested | ~~High~~ ✅ Fixed in v0.8.0 |
| #146 | Real-mode `get_instrument()` silently falls back to `GENERIC` for unknown driver types like `SIM` | ✅ Fixed in v0.8.0 |
| #147 | SIM-mode `driver_type="GENERIC"` silently mapped to `SimulatedMultimeter` | ✅ Fixed in v0.8.0 (`SimulatedGeneric` registered under `GENERIC`; `test_sim_generic_is_not_multimeter`) |
| #148 | No `GENERIC` key documented/discoverable in `DriverRegistry` | Open (partially addressed — GENERIC is registered; discoverability docs pending) |
| #149 | Broad `except Exception` during IDN probing hides real connection errors | ✅ Fixed in v0.9.0 |
| #150 | ASRL smart-probe sends vendor-specific TDK-Lambda commands to arbitrary serial devices | ✅ Fixed in v0.9.0 |
| #151 | `probe_resource` ASRL port-number filter uses naive substring match | ✅ Fixed in v0.8.0 |
| #152 | `_unsupported_feature` only prints a warning instead of using logging/raising | ✅ Fixed in v0.8.0 |
| #153 | `VisaDriver.query_value` returns 0.0 on error, ambiguous with a genuine 0.0 reading | ✅ Fixed in v0.8.0 (returns `None`; PR #181) |
| #154 | `UUTHandler.mes_voltage` silently returns 0.0 on a bad instrument response | ✅ Fixed in v0.9.x |
| #155 | `DataBroadcaster.send` swallows all exceptions with zero logging | ✅ Fixed in v0.8.0 |
| #156 | `Station.connect()` double-connects instruments already connected by `get_instrument()` | ✅ Fixed in v0.8.0 |
| #157 | `check_errors` has a test-detection hack embedded in production code | ✅ Fixed in v0.8.0 |
| #158 | ROADMAP.md bug table entries stale vs. actual code state | ✅ Fixed (this document) |
| #159 | AUTO-discovery candidate sort key is a naive boolean, not a transport-tier rank | ✅ Fixed in v0.9.0 |
| #160 | Simulated-driver filtering relies on fragile class-name string matching | ✅ Fixed in v0.9.x (`is_simulated` class flag) |
| #161 | Global VISA resource-manager singleton has no close/reset API | ✅ Fixed in v0.9.0 (`factory.close_rm()`) |
| #162 | `InstrumentDriver` non-abstract methods raise `NotImplementedError` at runtime instead of instantiation | ✅ Fixed in v0.8.0 |
| #163 | `VisaDriver.write` and `query_value` have inconsistent error-handling | ✅ Fixed in v0.9.0 |
| #164 | UUTHandler deprecation notice is stale (promised removal in v0.3.0) | ✅ Fixed in v0.8.0 |
| #165 | `config.py get_config()` is an unfinished stub that doesn't load files | ✅ Fixed in v0.8.0 (loads JSON/YAML) |
| #166 | Dynamic `async_` attribute wrapper has no validation, can mask typos | ✅ Fixed in v0.8.0 |
| #167 | Shared driver classes across models lack a documented compatibility matrix | ✅ Fixed in v0.9.0 (`docs/supported_instruments.md`) |
| #168 | `find_duplicate_addresses` edge cases beyond empty-list (identical descriptions, type-aware identity) | ✅ Fixed in v0.8.0 |

---

## Other Improvements

- **Type hints:** `utils.py`, `scanner.py`, `transport.py` fully annotated (gh #128) ✅
- **Docstrings:** All public functions have NumPy-style docstrings (gh #129) ✅
- **CI:** GitHub Actions workflow runs pytest on Python 3.9–3.13 (`main.yml`) ✅
- **Linting:** `ruff check` runs in CI (gh #126) ✅

---

## Stretch Goals (if time permits)

- [ ] `instrument.measure_all()` — single call to measure voltage, current, power simultaneously
- [ ] Plugin system for custom dashboard widgets
- [ ] TLS support for remote dashboard access

---

## Version Planning

| Version | Milestone |
| --- | --- |
| 0.7.0 | Bug fixes + hardening (released) |
| 0.8.0 | Generic driver fallback, PXA N9030A expansion, station/transport/logging hardening (released) |
| 0.9.0 | Driver-factory + simulation fixes (#149–#168 batch), ROADMAP reconciliation (in progress) |
