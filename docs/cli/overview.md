# Headstart: Mastering the CLI

The **Instrumation CLI** is more than just a helper; it's a powerful tool for rapid prototyping, hardware troubleshooting, and automation without writing a single line of Python.

## 1. Discovery and Exploration

Before writing code, you need to know what's connected to your system.

### Scanning for Instruments
This command polls all available VISA backends and Serial ports to find your equipment.

```bash
instrumation scan
```

### Checking an Identity
Instantly verify you can talk to an instrument at a specific address:

```bash
instrumation measure "USB0::0x2A8D::0x0101::MY59000123::0::INSTR" DMM get_id
```

---

## 2. Manual Control (On-the-Fly)

You can perform any driver method directly from the terminal. This is perfect for verifying a 5V rail or checking a signal peak.

### Measuring Voltage
```bash
instrumation measure "ADDR" DMM measure_voltage
```

### Checking a Signal Peak (Spectrum Analyzer)
```bash
instrumation measure "ADDR" SA get_peak_value
```

### JSON Output for Scripts
If you want to use the CLI result in a bash script or another tool, use the `--json` flag:

```bash
instrumation measure "ADDR" DMM measure_voltage --json
```

---

## 3. Station Management

Stations allow you to group multiple instruments into a single logical "Test Station" using a `station.toml` file.

### Listing Station Configuration
```bash
instrumation station list
```

### Measuring from a Station
Instead of providing a long VISA address, use the alias defined in your config:

```bash
# Assuming 'my_dmm' is an alias in station.toml
instrumation measure my_dmm DMM measure_voltage
```

---

## 4. The "Golden Master" Workflow

The CLI is the entry point for our powerful Record & Replay system.

### Phase 1: Record
Connect to your hardware and perform a sequence of manual queries. Everything is logged.

```bash
instrumation record "ADDR" DMM golden_run.json
```
*Type commands like `MEAS:VOLT?` or `*IDN?`. Type `quit` to save.*

### Phase 2: Verify
Check the contents of your recorded "Golden Master":
```bash
cat golden_run.json
```

### Phase 3: Headstart Replay
Run a measurement against the recording instead of the real hardware:

```bash
instrumation measure "replay://golden_run.json" DMM measure_voltage
```

---

## 5. Pro-Tips for Speed

### Use Simulation Mode
Test your entire command pipeline without any hardware by setting an environment variable:

```bash
# Windows
$env:INSTRUMATION_MODE="SIM"
instrumation scan
```

### Help System
Every command and subcommand has its own help page:
```bash
instrumation measure --help
instrumation station --help
```
