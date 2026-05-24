# Welcome to Instrumation

**Instrumation** is a powerful, modern Hardware Abstraction Layer (HAL) for RF test stations. It allows you to control complex lab equipment (DMMs, Network Analyzers, Signal Generators, etc.) using a simple, unified Python API.

!!! success "Key Feature: Digital Twins"
    Develop and test your automation scripts without actual hardware using built-in high-fidelity simulation drivers.

## Main Features

- **Intelligent Discovery**: Automatically find instruments over HiSLIP, USB, or GPIB with one-click `"AUTO"` addresses.
- **Virtual Front Panel (VFP)**: Real-time web dashboard for visualizing traces and instrument health.
- **Async Support**: Native parallel execution for high-speed automated test sequences.
- **Golden Master**: Record real hardware sessions and replay them later for deterministic testing.
- **Plugin System**: Dynamically load community-developed drivers from any directory.

---

## Real Hardware Validation

Instrumation has been validated against real lab equipment. Check out our experiment reports:

- [🔬 AFG ↔ DSOX Loopback](experiments/afg_dso_loopback.md) — Plug-and-play AUTO discovery with Tektronix AFG + Keysight DSOX
- [📡 PXA N9030A Validation](experiments/pxa_validation.md) — High-speed 32-bit binary trace transfers
- [🎛️ MXG N5183B Validation](experiments/mxg_validation.md) — Pulse modulation and frequency sweeps
- [📊 PNA N5232A Validation](experiments/vna_validation.md) — S-parameter measurements and Smith charts

---

## PyVISA vs Instrumation

See how Instrumation eliminates boilerplate when programming a signal generator:

| Aspect | PyVISA (raw SCPI) | Instrumation |
| :--- | :--- | :--- |
| **Discovery** | Manual — find the resource string | **Auto** — just pass `"AUTO"` |
| **Connection** | `rm.open_resource("TCPIP0::...")` with hardcoded address | `connect_instrument("AUTO", "SG")` — type-aware routing |
| **Configuration** | `sg.write(":FREQ:CW 2.4e9")` — raw SCPI strings | `sg.set_frequency(2.4e9)` — typed method with validation |
| **Cleanup** | Manual `sg.close()` — easy to forget | Context manager — automatic `with` block |
| **Offline Dev** | Requires real hardware | Digital Twin — set `INSTRUMATION_MODE=SIM` |
| **Portability** | Vendor-specific SCPI for each brand | **One API** — works on Keysight, Rigol, Tektronix, Siglent, R&S, Anritsu |

### Side-by-Side Code

```python
# PyVISA: 8 lines, manual config, raw SCPI
import pyvisa
rm = pyvisa.ResourceManager()
sg = rm.open_resource("TCPIP0::192.168.1.100::inst0::INSTR")
sg.write("*RST")
sg.write(":FREQ:CW 2.4e9")
sg.write(":POW:AMPL -10")
sg.write(":OUTP ON")
sg.close()

# Instrumation: 5 lines, zero config, type-safe
from instrumation import connect_instrument

with connect_instrument("AUTO", "SG") as sg:
    sg.set_frequency(2.4e9)
    sg.set_amplitude(-10)
    sg.set_output(True)
```

No resource manager. No SCPI strings. No hardcoded addresses. Just your test logic.

---

## Quick Install

```bash
pip install instrumation
```

## Simple Example

```python
from instrumation.factory import get_instrument

# Works with real hardware or simulation
with get_instrument("AUTO", "DMM") as dmm:
    result = dmm.measure_voltage()
    print(f"Measured: {result.value} {result.unit}")
```

## Next Steps

- Check out the [Installation Guide](getting_started/installation.md)
- Learn about [Simulation Mode](user_guide/simulation.md)
- See our [Hardware Experiments](experiments/afg_dso_loopback.md)
- Dive into the [API Reference](api_ref/index.md)
