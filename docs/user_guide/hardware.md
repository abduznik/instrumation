# Hardware Connection

This page explains how to connect to physical instruments.

## VISA Implementation
You have two main paths for connecting your instruments:

1. **Vendor Backend**: Use NI-VISA or Keysight IO Libraries. Mandatory for **GPIB** hardware and high-performance automated testing.
2. **Python Backend (`pyvisa-py`)**: Use for **Ethernet (TCPIP)**, **USB**, or **Serial**. This uses raw sockets and doesn't require extra software installation.

## Connection Strings
Addresses typically follow the VISA standard:
- **USB**: `USB0::0x2A8D::0x0101::MY12345678::0::INSTR`
- **TCP/IP**: `TCPIP0::192.168.1.10::inst0::INSTR`
- **GPIB**: `GPIB0::7::INSTR`

Starting with **v0.2.0**, the HAL includes an intelligent priority engine for `"AUTO"` resolution. It automatically scans your system using a multi-layer approach:

1. **Standard VISA Scan**: Finds all USB-TMC and ASRL devices.
2. **Smart LAN Probe (New)**: Performs a non-destructive ARP scan of the local subnet (`169.254.x.x` and `192.168.x.x`) to find instruments that don't broadcast their presence.
3. **Type-Aware Routing**: Probes each candidate with `*IDN?` and only selects the one matching your requested category (e.g., `SCOPE`, `SG`).

### Critical Device Setup
For certain instruments, you must enable specific I/O modes on the front panel for they to be discoverable:

- **Keysight DSOX/MSOX**: Ensure **USB Compatibility Mode** (or **USB-TMC**) is enabled in the `[Utility] -> I/O -> USB` menu. Without this, the instrument may appear as a "Printer" and will be invisible to the HAL.
- **Tektronix AFG**: Ensure the **VXI-11** server is active in the network configuration for LAN discovery.

### Usage Recommendation
Always try `"AUTO"` first to keep your scripts portable:

```python
# The HAL will find your Signal Generator automatically
sg = get_instrument("AUTO", "SG")
```

> [!TIP]
> If your instrument is on a different subnet or has discovery disabled, you can always fall back to an explicit IP: `TCPIP0::169.254.x.x::inst0::INSTR`.
