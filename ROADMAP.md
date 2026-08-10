# Roadmap — v0.7.0

**Target Release:** Q3 2026

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
| 0.7.0-alpha | Dashboard prototype + bug fixes |
| 0.7.0-beta | Dashboard stable + docs |
| 0.7.0 | Release |
