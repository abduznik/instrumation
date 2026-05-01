# Measuring from the CLI

The `measure` command allows you to execute any method defined in a driver directly from your terminal.

## Basic Syntax

```bash
instrumation measure <ADDRESS> <TYPE> <METHOD>
```

### Examples

**Measure DC Voltage on a DMM:**
```bash
instrumation measure "ADDR" DMM measure_voltage
```

**Get Peak Power on a Spectrum Analyzer:**
```bash
instrumation measure "ADDR" SA get_peak_value
```

**Set Output Frequency on a Signal Generator:**
```bash
instrumation measure "ADDR" SG set_frequency 1.5e9
```

## Advanced Options

### JSON Output
For integration with external tools (like Node-RED or custom dashboards), you can output the measurement result as a clean JSON object:

```bash
instrumation measure "ADDR" DMM measure_voltage --json
```

**Sample Output:**
```json
{
  "value": 5.001,
  "unit": "V",
  "status": "OK",
  "timestamp": "2026-05-01T10:48:00Z"
}
```

### Verbose Mode
Use `-v` to see the underlying SCPI commands being sent and received:
```bash
instrumation -v measure "ADDR" DMM measure_voltage
```
