# Quick Start

Get up and running with Instrumation in less than a minute.

## 1. Verify Simulation
Ensure you can run in simulation mode:
```bash
export INSTRUMATION_MODE=SIM
instrumation scan
```

## 2. Basic Script
Create a file named `test_hal.py`:
```python
from instrumation.factory import get_instrument

with get_instrument("AUTO", "DMM") as dmm:
    print(f"ID: {dmm.get_id()}")
```

## 3. Run it
```bash
python test_hal.py
```
