# TDK-Lambda Z+ Series Power Supply

This document details the integration and troubleshooting of the TDK-Lambda Z+ series PSU (specifically the Z+100-2 variant) within the `instrumation` HAL.

## 🗝️ Key Discovery: The "Handshake"
The TDK-Lambda Z+ uses a non-standard SCPI activation sequence when connected via Serial-over-USB. By default, the unit may appear unresponsive to standard `*IDN?` queries until it is placed in the correct SCPI mode.

### 1. Mandatory Preamble
Before any identification can occur, the following command must be sent:
```scpi
INST:NSEL 6
```
This selects the SCPI sub-system for the specific unit. Without this, the instrument often returns `VI_ERROR_TMO` (Timeout).

### 2. Line Termination
The Z+ is strict about line endings. It requires **CRLF** (`\r\n`) for both reading and writing. Standard `\n` alone will fail.

### 3. Connection Parameters
*   **Baud Rate**: 9600 (Standard factory default)
*   **Parity**: None
*   **Data Bits**: 8
*   **Stop Bits**: 1

## 💻 Driver Implementation
The driver is located at [`src/instrumation/drivers/tdk.py`](file:///Users/yan/Documents/instrumation/src/instrumation/drivers/tdk.py).

### Core Features
*   **Automatic Handshake**: The `connect()` method automatically sends `INST:NSEL 6` and waits for the internal controller to stabilize.
*   **Safety Overrides**: Implements `set_ocp`, `set_ovp`, and `clear_protection` for hardware-level safety latches.
*   **Standard API**: Fully aliased to the `PowerSupply` base class (`set_voltage`, `set_current`, etc.).

## 🧪 Validation Example
We used the following script to verify the "AUTO" discovery and control logic:

```python
from instrumation.factory import get_instrument

# The HAL now finds the PSU automatically using the Nitro-Cache
psu = get_instrument("AUTO", "PSU")

print(f"Connected to: {psu.get_id()}")

# Safety first
psu.set_voltage(0.0)
psu.set_output(True)

# Ramp test
for v in [1.0, 5.0, 12.0]:
    psu.set_voltage(v)
    print(f"Setting Voltage to {v}V... Actual: {psu.measure_voltage_actual().value}V")

psu.shutdown_safety()
```

## 🏎️ Performance Optimizations
Thanks to the **Nitro Cache** implemented in `factory.py`, once the PSU is identified once, subsequent connections bypass the 10-second NI-VISA scan and connect in **< 500ms**.

### Troubleshooting Logs
If the PSU is not found, check the `.visa_cache.json` file in the root directory. If the hardware port (e.g., `ASRL5::INSTR`) has changed due to a loose USB cable, delete the cache or wait for the "Slow Track" scan to finish.
