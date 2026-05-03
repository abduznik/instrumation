# Experiment: TDK-Lambda Z+ PSU Integration and Handshake Validation

This document summarizes the integration and verification of the TDK-Lambda Z+ series power supply (Z+100-2) within the HAL. This experiment identified critical hardware and software configuration requirements for stable USB communication.

## Hardware Setup
- **Instrument**: TDK-Lambda Z+100-2 Power Supply.
- **Connection**: USB (Serial-over-USB).
- **Interface**: Internal FTDI Serial Bridge.

## Essential Device Configuration

### 1. Front Panel Physical Setup (The "USB Mode" Fix)
By default, many Z+ units are configured for RS232/RS485 communication via the rear DB-sub connector. The USB port will appear dead unless the interface is explicitly switched to USB mode on the front panel.

> [!IMPORTANT]
> **Switching to USB Mode**:
> 1. Press the **[REM/LOC]** button until the display shows the configuration menu.
> 2. Rotate the **[VOLTAGE]** encoder until you find the `IF` (Interface) menu.
> 3. Press the encoder to enter, and rotate until `USB` is displayed.
> 4. Press the encoder again to confirm. 
> 5. **Power Cycle**: It is recommended to restart the unit after changing the interface mode.

### 2. SCPI Handshake (INST:NSEL)
Even in USB mode, the unit remains in a "dormant" SCPI state.
- **Mandatory Command**: `INST:NSEL 6` must be the first command sent.
- **Effect**: This selects the specific instrument channel for the SCPI parser. Without this, the unit will not respond to `*IDN?`.

### 3. Communication Parameters
- **Baud Rate**: 9600 (Must match the value set in the front panel `BAUD` menu).
- **Line Termination**: Strictly `\r\n` (CRLF).

## Results and Performance
The integration of these physical and software fixes resulted in a robust connection that survives instrument restarts.

### Discovery Latency
| Method | Latency | Status |
| --- | --- | --- |
| Cold Scan (Full NI-VISA) | ~10.6 seconds | Pass |
| Cached Discovery (Nitro) | ~0.45 seconds | Pass |

## Verification Example
```python
from instrumation.factory import get_instrument

# Ensure the PSU is set to USB mode on the front panel before running
psu = get_instrument("AUTO", "PSU")
print(f"Verified Connection: {psu.get_id()}")

psu.set_voltage(5.0)
psu.set_output(True)
psu.shutdown_safety()
```
