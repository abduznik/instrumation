## Support This Project

> **All projects made with passion** 💙

[![Sponsor me](https://img.shields.io/badge/❤️%20Sponsor-GitHub-red?style=for-the-badge)](https://github.com/sponsors/abduznik)

# Instrumation

[![PyPI version](https://img.shields.io/pypi/v/instrumation)](https://pypi.org/project/instrumation/)
[![License](https://img.shields.io/pypi/l/instrumation)](https://pypi.org/project/instrumation/)
[![Python Versions](https://img.shields.io/pypi/pyversions/instrumation)](https://pypi.org/project/instrumation/)
[![Stars](https://img.shields.io/github/stars/abduznik/instrumation?style=flat)](https://github.com/abduznik/instrumation/stargazers)
[![Downloads](https://static.pepy.tech/personalized-badge/instrumation?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/instrumation)

![Example](assets/example.gif)

A high-level Hardware Abstraction Layer (HAL) for RF test stations. Stop wrestling with PyVISA boilerplate — write test logic, not connection code.

---

## Why Instrumation?

RF test bench automation is painful. Every instrument brand has its own quirks, SCPI dialects vary, and testing your scripts requires physical hardware on your desk. Instrumation fixes all three:

- **One API for everything** — same code works on Keysight, Rigol, and any other supported brand
- **Digital Twin mode** — develop and debug offline with simulated instruments that emit realistic Gaussian noise
- **Smart auto-detection** — scans connected devices and loads the right driver automatically, no manual config

---

## Real Hardware Validation

Instrumation has been validated against real lab hardware. See our experiment reports:

- [🔬 AFG ↔ DSOX Loopback Validation](https://abduznik.github.io/instrumation/experiments/afg_dso_loopback/) — Plug-and-play AUTO discovery with Tektronix AFG3022C + Keysight DSOX2002A
- [📡 PXA N9030A Spectrum Analyzer](https://abduznik.github.io/instrumation/experiments/pxa_validation/) — 32-bit binary trace transfers at high speed
- [🎛️ MXG N5183B Signal Generator](https://abduznik.github.io/instrumation/experiments/mxg_validation/) — Pulse modulation and frequency sweeps
- [📊 PNA N5232A Network Analyzer](https://abduznik.github.io/instrumation/experiments/vna_validation/) — S-parameter measurements and Smith charts

---

## PyVISA vs Instrumation: See the Difference

Programming a signal generator the traditional way vs. with Instrumation:

| Aspect | PyVISA (raw SCPI) | Instrumation |
| :--- | :--- | :--- |
| **Discovery** | Manual — find the resource string, manage `ResourceManager` | **Auto** — just pass `"AUTO"` and the HAL scans USB + LAN for you |
| **Connection** | `rm.open_resource("TCPIP0::192.168.1.100::...")` — hardcoded address | `connect_instrument("AUTO", "SG")` — type-aware routing |
| **Configuration** | `sg.write(":FREQ:CW 2.4e9")` — raw SCPI strings, no validation | `sg.set_frequency(2.4e9)` — typed method with bounds checking |
| **Cleanup** | Manual `sg.close()` — easy to forget | Context manager — automatic `with` block cleanup |
| **Offline Dev** | Requires real hardware connected | Digital Twin — set `INSTRUMATION_MODE=SIM` and develop anywhere |
| **Portability** | Vendor-specific SCPI — rewrite for each brand | **One API** — works on Keysight, Rigol, Tektronix, Siglent, R&S, Anritsu |

### Side-by-Side Code

```python
# ─── PyVISA: 8 lines of boilerplate ───
import pyvisa
rm = pyvisa.ResourceManager()
# Manually find the right resource...
sg = rm.open_resource("TCPIP0::192.168.1.100::inst0::INSTR")
sg.write("*RST")
sg.write(":FREQ:CW 2.4e9")
sg.write(":POW:AMPL -10")
sg.write(":OUTP ON")
sg.close()

# ─── Instrumation: 5 lines, zero config ───
from instrumation import connect_instrument

with connect_instrument("AUTO", "SG") as sg:
    sg.set_frequency(2.4e9)
    sg.set_amplitude(-10)
    sg.set_output(True)
```

No resource manager. No SCPI strings. No hardcoded addresses. Just your test logic.

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
from instrumation.factory import get_instrument

# Safer usage with context manager
with get_instrument("DUMMY_ADDRESS", "DMM") as dmm:
    print(dmm.get_id())
    result = dmm.measure_voltage()
    print(f"Voltage: {result}")
```

---

## Station Manager (TOML)

Manage complex test stations with multiple instruments using a `station.toml` file.

```toml
[instruments.sa_main]
driver = "SA"
address = "USB0::0x2A8D::0x0101::MY12345678::0::INSTR"

[instruments.psu_dut]
driver = "PSU"
address = "TCPIP0::192.168.1.100::inst0::INSTR"
```

Use it in your code:

```python
from instrumation import Station

station = Station("station.toml")
station.connect()

# Access instruments via dot notation
res = station.instr.sa_main.get_peak_value()
print(f"Peak: {res}")

station.disconnect()
```

---

## Command Line Interface

Instrumation comes with a powerful CLI for quick interaction and diagnostics.

```bash
# Scan for connected hardware
instrumation scan

# Take a quick measurement
instrumation measure USB0::... DMM measure_voltage

# List instruments in your station.toml
instrumation station list

# Measure using a named instrument from your station
instrumation station measure sa_main get_peak_value
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
