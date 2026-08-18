# Roadmap — v0.8.0

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
- SIM-mode `driver_type="GENERIC"` now returns `SimulatedGeneric`, not `SimulatedMultimeter`.
- Added mocked-VISA regression tests for IDN routing, the no-match fallback, and the ASRL/TDK-Lambda smart probe (`tests/test_factory_routing.py`).

### Why it matters

Sending a brand's vendor-specific SCPI commands to an instrument that never claimed to speak that dialect can produce wrong results or trigger hardware errors silently. Unrecognized instruments now get safe, generic SCPI access instead of a guessed brand driver.

---

## New Feature: Live Instrument Dashboard

A lightweight, browser-based real-time dashboard that displays connected instruments, their status, and live measurement readings. Built on the existing `DataBroadcaster` (UDP) infrastructure with zero external dependencies beyond `websockets`.

### What it does

- Auto-discovers instruments and shows them in a clean table
- Streams live readings (voltage, current, frequency, etc.) to the browser in real-time
- Color-coded status indicators (connected, measuring, error, idle)
- Export readings to CSV/JSON with one click
- Works in SIM mode for demos and development

### Why it matters

Lab engineers currently copy-paste readings into spreadsheets. A live dashboard eliminates manual data collection and gives instant visibility into what every instrument in the rack is doing.

### Architecture

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

| Issue | Description | Priority |
| --- | --- | --- |
| #142 | Add a real `GenericDriver` fallback for unrecognized instruments | ~~High~~ ✅ Fixed in v0.8.0 |
| #143 | Unknown-IDN instrument could silently receive the wrong brand-specific driver | ~~High~~ ✅ Fixed in v0.8.0 |
| #144 | `connect_instrument()` hardcoded DMM as fallback for any unrecognized instrument | ~~High~~ ✅ Fixed in v0.8.0 |
| #145 | `factory.py`'s real-hardware IDN-routing and discovery paths were untested | ~~High~~ ✅ Fixed in v0.8.0 |
| #120 | `connect_instrument()` swallows `ConfigurationError` — should propagate | ~~High~~ ✅ Fixed in v0.7.0 |
| #121 | `find_duplicate_addresses` doesn't handle empty scan list | Medium |
| #122 | Async wrapper leaks connections on `KeyboardInterrupt` | ~~High~~ ✅ Fixed in v0.7.0 |
| #123 | `get_instrument()` cache file `.visa_cache.json` not created on first run | ~~Low~~ ✅ Fixed in v0.6.0 |
| #124 | `poll_for_mav` blocks event loop when used in async context | Medium |
| #125 | `batch_query` should support `write_then_read` pattern (no query) | Low |
| #135 | `get_instrument()` manual connection cache update fails with `UnboundLocalError` | ~~High~~ ✅ Fixed in v0.7.0 |

---

## Other Improvements

- **Type hints:** Add full type annotations to `utils.py`, `scanner.py`, `transport.py`
- **Docstrings:** Ensure all public functions have NumPy-style docstrings
- **CI:** Add GitHub Actions workflow for automated testing on Python 3.8–3.13
- **Linting:** Add `ruff` check to CI pipeline

---

## Stretch Goals (if time permits)

- [ ] `instrument.measure_all()` — single call to measure voltage, current, power simultaneously
- [ ] Plugin system for custom dashboard widgets
- [ ] TLS support for remote dashboard access

---

## Version Planning

| Version | Milestone |
| --- | --- |
| 0.7.0 | Dashboard prototype + bug fixes (released) |
| 0.8.0-alpha | Generic driver fallback + factory routing fixes/tests |
| 0.8.0 | Release |
