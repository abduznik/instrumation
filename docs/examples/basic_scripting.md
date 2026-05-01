# Example: Basic Scripting

This example shows the most common way to use Instrumation in a Python script.

## Goal
Connect to a Digital Multimeter, set it up for DC Voltage, and take 5 readings.

## The Script
```python
import time
from instrumation.factory import get_instrument

# 1. Connect (Auto-discovery for first DMM found)
with get_instrument("AUTO", "DMM") as dmm:
    
    print(f"Connected to: {dmm.get_id()}")
    
    # 2. Take multiple measurements
    for i in range(5):
        result = dmm.measure_voltage()
        print(f"Reading {i+1}: {result.value} {result.unit}")
        time.sleep(0.5)

# 3. Clean exit (handled by context manager)
print("Done.")
```

## Running in Simulation
To test this script without hardware, simply set:
```bash
export INSTRUMATION_MODE=SIM
python my_script.py
```
