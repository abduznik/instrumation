# Simulation (Digital Twins)

One of the unique features of Instrumation is the ability to write code using "Digital Twins". This allows you to develop your automation scripts at home or in the office, and then take them to the lab when ready.

## Enabling Simulation Mode

To enable simulation mode, set the `INSTRUMATION_MODE` environment variable to `SIM`.

=== "Windows (PowerShell)"
    ```powershell
    # Enable SIM mode
    $env:INSTRUMATION_MODE="SIM"
    
    # Revert to REAL mode (or just unset)
    $env:INSTRUMATION_MODE="REAL"
    # OR
    Remove-Item Env:INSTRUMATION_MODE
    ```

=== "macOS / Linux"
    ```bash
    # Enable SIM mode
    export INSTRUMATION_MODE="SIM"
    
    # Revert to REAL mode
    export INSTRUMATION_MODE="REAL"
    # OR
    unset INSTRUMATION_MODE
    ```

## How it Works

When `INSTRUMATION_MODE` is set to `SIM`, the `get_instrument` factory will return a `Simulated` version of the driver you requested.

### Example
```python
from instrumation.factory import get_instrument

# In SIM mode, this returns a SimulatedSpectrumAnalyzer
with get_instrument("AUTO", "SA") as sa:
    res = sa.get_peak_value()
    print(f"Simulated Peak: {res.value} {res.unit}")
```

## Configurable Latency
Real hardware has transport delays (GPIB, LAN). You can simulate this in your tests:

```python
sa = get_instrument("AUTO", "SA")
sa.latency = 0.5  # Add 500ms delay to every command
```
