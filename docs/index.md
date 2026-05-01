# Welcome to Instrumation

**Instrumation** is a powerful, modern Hardware Abstraction Layer (HAL) for RF test stations. It allows you to control complex lab equipment (DMMs, Network Analyzers, Signal Generators, etc.) using a simple, unified Python API.

!!! success "Key Feature: Digital Twins"
    Develop and test your automation scripts without actual hardware using built-in high-fidelity simulation drivers.

## Main Features

- Asynchronous Support: Take measurements from multiple instruments in parallel with `asyncio`.
- Golden Master: Record real hardware sessions and replay them later for deterministic testing.
- Plugin System: Easily add or load community-developed drivers without modifying the core.
- Cross-Platform: Works on Windows, Linux, and macOS (including ARM64).
- CLI Interface: Quick hardware verification and measurement from the command line.

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
