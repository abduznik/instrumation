# Experiment: TDK-Lambda Z+ PSU Integration and Handshake Validation

This document summarizes the integration and verification of the TDK-Lambda Z+ series power supply (Z+100-2) within the HAL. The focus was on resolving communication timeouts and implementing high-speed discovery.

## Hardware Setup
- **Instrument**: TDK-Lambda Z+100-2 Power Supply.
- **Connection**: USB (Serial-over-USB) via FTDI interface.
- **Port Settings**: 9600 Baud, 8N1, CRLF Termination.

## Essential Device Configuration
To enable SCPI communication on the Z+ series via the USB port, specific initialization sequences are required.

### SCPI Handshake (INST:NSEL)
> [!IMPORTANT]
> **Mandatory Command**: The Z+ controller often defaults to a non-responsive state on the USB bus. 
> 1. The command `INST:NSEL 6` must be sent as the very first instruction after opening the resource.
> 2. A small delay (min 200ms) is required after this command before sending `*IDN?`.

### Line Termination
> [!WARNING]
> **CRLF Required**: The Z+ series strictly requires `\r\n` (CRLF) for both read and write operations. Standard `\n` line endings will result in communication timeouts.

## Results and Performance
With the implementation of the Nitro-Cache and parallel probing engine, the PSU discovery performance has been significantly improved.

### Discovery Latency
| Method | Latency | Status |
| --- | --- | --- |
| Cold Scan (Full NI-VISA) | ~10.6 seconds | Pass |
| Cached Discovery (Nitro) | ~0.45 seconds | Pass |

## Verification Example
The following snippet verifies the SCPI control loop:

```python
from instrumation.factory import get_instrument

# HAL automatically handles the NSEL 6 handshake
psu = get_instrument("AUTO", "PSU")
psu.set_voltage(5.0)
psu.set_output(True)

actual = psu.measure_voltage_actual()
print(f"Set: 5.0V, Measured: {actual.value}V")
psu.shutdown_safety()
```
