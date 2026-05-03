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

- Check out the [Installation Guide](installation.md)
- Learn about [Simulation Mode](simulation.md)
- Dive into the [API Reference](api.md)
