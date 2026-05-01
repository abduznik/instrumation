# Instrumation Hardware Usage Guide

This guide explains how to use Instrumation with actual hardware and verify your setup.

## 1. Prerequisites (Real Hardware Only)

To communicate with physical instruments over USB, GPIB, or LAN, you need a VISA implementation installed on your machine:

- **Windows:** [NI-VISA](https://www.ni.com/en/support/downloads/drivers/download.ni-visa.html) or [Keysight IO Libraries Suite](https://www.keysight.com/us/en/lib/software-detail/computer-software/io-libraries-suite-downloads-2175637.html).
- **Linux:** `pyvisa-py` (usually installed via pip) and `libusb`.

## 2. Quick Verification (CLI)

The fastest way to check if Instrumation "sees" your hardware is the CLI:

```bash
# 1. List all connected instruments
instrumation scan

# 2. Try to read an IDN string from a specific address
# Replace the address with one found in the scan
instrumation measure "USB0::0x2A8D::0x0101::MY12345678::0::INSTR" DMM get_id
```

## 3. Connecting via Python

### Option A: The "Smart" Way (Auto-Discovery)
If you only have one instrument of a specific type connected, you can let Instrumation find it:

```python
from instrumation.factory import get_instrument

# This will scan for a DMM and return the correct driver (Keithley, etc.)
with get_instrument("AUTO", "DMM") as dmm:
    print(f"Connected to: {dmm.get_id()}")
    res = dmm.measure_voltage()
    print(f"Reading: {res.value} {res.unit}")
```

### Option B: Explicit Address
If you know the VISA address:

```python
from instrumation.factory import get_instrument

address = "TCPIP0::192.168.1.100::inst0::INSTR"
with get_instrument(address, "SA") as sa:
    peak = sa.get_peak_value()
    print(f"Peak Power: {peak.value} {peak.unit}")
```

## 4. How to be sure it works?

Since we are developing without the instrument right now, we use several layers of verification:

1.  **Simulated Drivers**: These are "Digital Twins" that implement the exact same SCPI command set as the real hardware. When you run in `SIM` mode, the HAL behaves exactly as it would with real hardware, but returns simulated data.
2.  **Unit Tests**: We have 60+ tests that verify every driver method against these simulated responses.
3.  **Golden Master**: You can record a real session once you have the instrument, and then use that recording to "replay" the session later for testing without the hardware.

### To Record a Real Session:
```bash
instrumation record "USB0::..." DMM my_dmm_master.json
```

### To Replay later (No Hardware needed):
```python
from instrumation.factory import get_instrument

# Use the replay:// protocol
with get_instrument("replay://my_dmm_master.json", "DMM") as dmm:
    print(dmm.measure_voltage()) # Returns exactly what was recorded
```

## 5. Troubleshooting

- **"Resource Not Found":** Ensure your instrument is powered on and visible in NI-MAX or Keysight Connection Expert.
- **"Unknown Driver":** If your instrument isn't automatically recognized, ensure its `*IDN?` string contains one of the supported brands (Keysight, Rigol, Siglent, TDK, Keithley, Tektronix).
- **Timeout:** Check your connection cable and ensure no other software is using the instrument.
