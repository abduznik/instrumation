# Scanning and Discovery

The first step in any automation task is finding your hardware. The Instrumation CLI provides a unified way to see everything connected to your system.

## The Scan Command

Run the following to poll all VISA backends (NI-VISA, Keysight, pyvisa-py) and Serial ports:

```bash
instrumation scan
```

### Understanding the Output
The output is grouped by connection type:
- **USB**: LXI and USBTMC instruments.
- **TCPIP**: Ethernet-connected instruments.
- **GPIB**: Traditional bus instruments.
- **Serial**: COM ports (often used for TDK-Lambda or Arduino-based controllers).

## Checking an Identity

If you know the address but want to verify the instrument type and model, use the `get_id` method:

```bash
instrumation measure "USB0::0x2A8D::0x0101::MY123456::0::INSTR" DMM get_id
```

This sends a `*IDN?` query and parses the manufacturer, model, and serial number.
