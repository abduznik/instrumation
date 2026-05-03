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

## Intelligent Auto-Discovery

Starting with **v0.2.0**, the HAL includes an intelligent priority engine for `"AUTO"` resolution. It automatically scans your system and prioritizes high-speed interfaces:

1. **TCPIP (HiSLIP/VXI-11)** - Prioritized for modern LXI hardware.
2. **USB** - Plug-and-play instruments.
3. **GPIB** - Legacy hardware.
4. **ASRL** - Serial/System ports (Filtered by default to avoid debug console conflicts).

### Usage Recommendation
Always try `"AUTO"` first to keep your scripts portable:

```python
# The HAL will find your Signal Generator automatically
sg = get_instrument("AUTO", "SG")
```

> [!TIP]
> If your instrument is on a different subnet or has discovery disabled, you can always fall back to an explicit IP: `TCPIP0::169.254.x.x::inst0::INSTR`.
