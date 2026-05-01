# Command Line Interface (CLI)

Instrumation includes a powerful CLI for quick hardware verification and basic automation without writing any code.

## Basic Usage

The primary command is `instrumation`. You can see all options with:

```bash
instrumation --help
```

## Commands

### 1. Scan for Hardware
Lists all instruments detected by your VISA implementation and Serial ports.

```bash
instrumation scan
```

### 2. Take a Measurement
Perform a single measurement on a specific instrument.

```bash
# Syntax: instrumation measure <address> <type> <method>
instrumation measure "USB0::0x2A8D::0x0101::MY12345678::0::INSTR" DMM measure_voltage
```

### 3. Manage Stations
Display information about instruments defined in your `station.toml`.

```bash
instrumation station list
```

### 4. Record a Session (Golden Master)
Enter an interactive SCPI session to record a "Golden Master" file.

```bash
instrumation record "ADDR" DMM my_recording.json
```

## Global Options

### Simulation Mode
You can force the CLI to run in simulation mode for testing your logic:

=== "Windows"
    ```powershell
    $env:INSTRUMATION_MODE="SIM"
    instrumation measure "ANY_ADDR" DMM measure_voltage
    ```

=== "macOS / Linux"
    ```bash
    export INSTRUMATION_MODE="SIM"
    instrumation measure "ANY_ADDR" DMM measure_voltage
    ```
