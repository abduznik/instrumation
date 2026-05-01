# Hardware Connection

This page explains how to connect to physical instruments.

## VISA Implementation
You must have a VISA library installed:
- **Windows**: NI-VISA or Keysight IO Libraries.
- **macOS/Linux**: `pyvisa-py`.

## Connection Strings
Addresses typically follow the VISA standard:
- **USB**: `USB0::0x2A8D::0x0101::MY12345678::0::INSTR`
- **TCP/IP**: `TCPIP0::192.168.1.10::inst0::INSTR`
- **GPIB**: `GPIB0::7::INSTR`

## Auto-Discovery
If you have only one instrument of a type connected, use `"AUTO"`:
```python
instr = get_instrument("AUTO", "DMM")
```
