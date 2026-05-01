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
