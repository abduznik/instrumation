# Instrumation

[![PyPI version](https://img.shields.io/pypi/v/instrumation)](https://pypi.org/project/instrumation/)
[![License](https://img.shields.io/pypi/l/instrumation)](https://pypi.org/project/instrumation/)
[![Python Versions](https://img.shields.io/pypi/pyversions/instrumation)](https://pypi.org/project/instrumation/)
[![Stars](https://img.shields.io/github/stars/abduznik/instrumation?style=flat)](https://github.com/abduznik/instrumation/stargazers)

![Example](assets/example.gif)

A high-level Hardware Abstraction Layer (HAL) for RF test stations. Stop wrestling with PyVISA boilerplate — write test logic, not connection code.

---

## Why Instrumation?

RF test bench automation is painful. Every instrument brand has its own quirks, SCPI dialects vary, and testing your scripts requires physical hardware on your desk. Instrumation fixes all three:

- **One API for everything** — same code works on Keysight, Rigol, and any other supported brand
- **Digital Twin mode** — develop and debug offline with simulated instruments that emit realistic Gaussian noise
- **Smart auto-detection** — scans connected devices and loads the right driver automatically, no manual config

---

--- 

## Live Data Streaming 

Instrumation includes a built-in `DataBroadcaster` for streaming live readings over UDP. This allows you to build real-time dashboards or loggers with zero external dependencies. 

- **Zero-lag** — UDP delivery doesn't block your test flow. 
- **Zero-config** — Broadcast to any host/port as JSON packets. 
- **Zero-dep** — Built-in with Python standard library. 

See [examples/broadcast_demo.py](examples/broadcast_demo.py) and [examples/dashboard.py](examples/dashboard.py) for usage. 

## Features

- **Auto-Discovery** — scans VISA and Serial buses, identifies what's connected
- **Smart Factory** — detects instrument brand and loads the correct driver
- **Digital Twin** — full simulation mode for offline development and CI pipelines
- **Unified API** — write once, run on any supported hardware
- **Built-in CSV logging** — test results logged out of the box

---

## Installation

```bash
pip install instrumation
```

Or install from source:

```bash
git clone https://github.com/abduznik/instrumation.git
cd instrumation
pip install .
```

> **Windows users:** You may need [NI-VISA](https://www.ni.com/en/support/downloads/drivers/download.ni-visa.html) or [Keysight IO Libraries Suite](https://www.keysight.com/us/en/lib/software-detail/computer-software/io-libraries-suite-downloads-2175637.html) for physical hardware access.

---

## Quick Start

### Real hardware

```python
import instrumation

sa = instrumation.connect_instrument("USB0::0x2A8D::...")

peak_power = sa.get_peak_value()
print(f"Peak Power: {peak_power} dBm")
```

### Digital Twin (no hardware needed)

```python
# Linux/macOS
export INSTRUMATION_MODE=SIM

# Windows PowerShell
$env:INSTRUMATION_MODE="SIM"
```

```python
from instrumation.factory import get_driver

driver = get_driver("DUMMY_ADDRESS")
driver.connect()

print(driver.get_id())
print(f"Voltage: {driver.measure_voltage(1)} V")
```

---

## API Reference

| Command | Description |
| :--- | :--- |
| `scan()` | Lists all connected Serial and VISA devices |
| `connect()` | Auto-connects to a generic Test Station (Box + Instrument) |
| `connect_instrument(addr)` | Connects to a specific instrument with auto driver detection |

---

## Platform Support

| Platform | Status |
| :--- | :--- |
| Windows | Supported |
| Linux | Supported |
| Termux (Android) | Supported |
| macOS | Supported |

---

## Development

```bash
# Install in editable mode (required for tests to pick up local changes)
pip install -e .
# This project uses pyproject.toml (PEP 517/518). No setup.py is required.


# Install test dependencies
pip install pytest flake8

# Run tests (simulation mode)
export INSTRUMATION_MODE=SIM  # Linux/macOS
pytest
```

---

## Tech Stack

- **Language:** Python 3.7+
- **Libraries:** PyVISA, PySerial
- **Architecture:** Smart Factory Pattern, Polymorphism
- **Standards:** SCPI (Standard Commands for Programmable Instruments)

---

## Support the Project

Instrumation is maintained in my spare time alongside a full-time RF technician job. If it's saved you hours of boilerplate or made your test bench easier to automate, consider supporting:

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-%E2%9D%A4-ea4aaa?logo=github)](https://github.com/sponsors/abduznik)

Commercial support or custom driver development? Reach out via GitHub Issues or Discussions.

---

## Contributing

PRs and driver contributions are welcome. Open an issue first to discuss larger changes.

## License

See [LICENSE](LICENSE) for details.
