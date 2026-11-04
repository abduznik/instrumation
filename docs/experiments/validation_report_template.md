# Validation Report Template

Use this template to validate an Instrumation driver against real hardware and
share the results with the project. Copy the file, fill it in, and submit it
by opening a **Validation report** issue
(<https://github.com/abduznik/instrumation/issues/new?template=validation_report.yml>)
— paste the completed report into the issue body, or attach a link to your
filled-in copy.

> [!TIP]
> You do not need to pass every check to submit. An honest partial result
> (e.g. "works on firmware A.10, fails on B.02") is valuable — it is exactly
> what the compatibility matrix is for.

---

## Report Metadata

| Field | Value |
|:---|:---|
| Driver (class name) | e.g. `KeysightPXA` |
| Driver version | e.g. `instrumation 0.9.0` (`pip show instrumation`) |
| Instrument model | e.g. Keysight N9030A |
| Serial number | e.g. US53310156 |
| Firmware revision | e.g. `A.14.04` (from `*IDN?`) |
| Connection | e.g. LAN (VXI-11), LAN (HiSLIP), USB-TMC, GPIB, Serial |
| Host OS / Python | e.g. Ubuntu 24.04, Python 3.12 |
| `*IDN?` response | paste verbatim |
| Date tested | e.g. 2026-11-04 |
| Validator (optional) | name / GitHub handle |

## Setup & Discovery

Describe how the instrument was connected and discovered:

- Was `"AUTO"` resolution used, or an explicit resource string?
- Did `connect_instrument()` pick the right driver automatically?
- Any front-panel configuration required before remote control worked
  (interface mode, USB-TMC compatibility mode, `INST:NSEL`, etc.)?

## Commands Exercised

List every driver method you called and whether it passed. At minimum,
exercise:

- [ ] `*IDN?` / `get_id()`
- [ ] `preset()` / reset
- [ ] One representative setpoint + readback per subsystem the driver covers
      (e.g. frequency + amplitude for an SG, `MEASure:` for a DMM)
- [ ] `check_errors()` returns no SCPI errors after the session
- [ ] `shutdown_safety()` (or equivalent cleanup) runs without error

| Method | Result | Notes |
|:---|:---|:---|
| `get_id()` | Pass / Fail | |
| `preset()` | Pass / Fail | |
| `measure_voltage()` | Pass / Fail | |
| ... | | |

## Results

- **Overall**: Pass / Partial / Fail
- **Measurement sanity check**: if you compared a reading against a known
  good reference, state the reference and the delta.
- **Throughput/latency notes** (optional): anything relevant for binary
  transfers, large sweeps, or settle times.

## Known Issues / Quirks

Document anything the driver had to work around or that users of the same
model should know: byte order for binary blocks, gated `DISP:` commands,
termination characters, mandatory first commands, front-panel lockouts, etc.

## Suggested Compatibility-Matrix Entry

Propose the exact row for `docs/supported_instruments.md`, e.g.:

```text
✅ 2026-11-04, FW A.14.04 (this report)
```

---

*By submitting this report you agree it may be published in the project's
documentation under the project's MIT license.*
