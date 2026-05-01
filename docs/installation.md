# Installation

## Basic Installation

You can install Instrumation directly from PyPI:

```bash
pip install instrumation
```

## Hardware Requirements

To communicate with physical instruments, you need a VISA implementation installed on your system.

### Windows
Download and install either:
- [NI-VISA](https://www.ni.com/en/support/downloads/drivers/download.ni-visa.html)
- [Keysight IO Libraries Suite](https://www.keysight.com/us/en/lib/software-detail/computer-software/io-libraries-suite-downloads-2175637.html)

### macOS (ARM64/Intel)
If you are on a Mac (like the MacBook Neo), install `pyvisa-py`:

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
