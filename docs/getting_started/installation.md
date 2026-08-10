# Installation

## Basic Installation

You can install Instrumation directly from PyPI:

```bash
pip install instrumation
```

## Hardware Requirements

To communicate with physical instruments, you have two options for the transport layer.

### Option 1: Vendor VISA (Recommended for Windows/GPIB)
Install a vendor VISA implementation for maximum performance and mandatory GPIB support:
- [NI-VISA](https://www.ni.com/en/support/downloads/drivers/download.ni-visa.html)
- [Keysight IO Libraries Suite](https://www.keysight.com/us/en/lib/software-detail/computer-software/io-libraries-suite-downloads-2175637.html)

### Option 2: Pure Python (Ethernet/USB/Serial)
If you are only using Ethernet (LAN) or USB/Serial, you can avoid heavy vendor software by using `pyvisa-py`. This uses raw sockets and native USB drivers:

```bash
pip install pyvisa-py psutil
```

## Simulation Mode (No Hardware)
If you only intend to use simulation for development, no additional drivers are required. Just set the environment variable:

=== "Windows (PowerShell)"
    ```powershell
    $env:INSTRUMATION_MODE="SIM"
    ```

=== "macOS / Linux"
    ```bash
    export INSTRUMATION_MODE="SIM"
    ```

## Packaging as a Windows .exe (PyInstaller)

If you package an Instrumation app as a single-file Windows `.exe`, note that part of the library is **dynamically loaded at runtime** rather than imported at the top of the file:

- `pyvisa_py` — the pure-Python VISA backend PyVISA uses when no vendor VISA library is installed.
- `instrumation.drivers.*` — device drivers discovered at runtime via `load_plugins()` and lazy imports.

PyInstaller only bundles what it can see by static analysis, so a default build will be **missing these modules**. The `.exe` starts fine but fails the moment it tries to connect, with errors such as:

```
ModuleNotFoundError: No module named 'pyvisa_py'
AttributeError: 'NoneType' object has no attribute 'rsplit'
```

Include them explicitly when building:

```bash
pyinstaller --onefile --windowed --name MyApp ^
  --collect-all pyvisa_py ^
  --hidden-import pyvisa_py.protocols.hislip ^
  --hidden-import pyvisa_py.protocols.vxi11 ^
  --collect-all instrumation ^
  app.py
```

> **Note for Windows:** Instrumation never passes `None` to `pyvisa.ResourceManager` (it passes an empty string), so PyVISA automatically selects system VISA if installed and falls back to the bundled `pyvisa_py` otherwise.
