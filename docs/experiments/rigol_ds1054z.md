# Experiment: Rigol DS1054Z Oscilloscope Integration

This document covers the integration of the Rigol DS1054Z (MSO1000Z/DS1000Z
family) into Instrumation. The DS1054Z is a 50 MHz, 4-channel digital
oscilloscope and one of the most popular entry-level scopes for hobby and
educational RF labs.

## Hardware Setup

- **Instrument**: Rigol DS1054Z (50 MHz, 4-ch, 1 GSa/s)
- **Firmware**: 00.04.03.00.03 (tested)
- **Connection**: USB-TMC (direct) or LAN (SCPI raw)

## Connection

### USB-TMC
Ensure the DS1054Z is connected via the rear-panel USB-B port and that USB
TMC is enabled (Menu → Utility → I/O → USB → TMC On).

```python
from instrumation import connect_instrument

scope = connect_instrument("USB0::0x1AB1::0x04CE::DS1054Z::INSTR", "SCOPE")
```

### LAN (SCPI Raw)
Enable LAN in Menu → Utility → I/O → LAN, then set a static IP or DHCP.

```python
scope = connect_instrument("TCPIP::192.168.1.100::INSTR", "SCOPE")
```

### Auto-Discovery
```python
scope = connect_instrument("AUTO", "SCOPE")
```

## Basic Usage

```python
from instrumation import connect_instrument

with connect_instrument("AUTO", "SCOPE") as scope:
    print(scope.get_id())  # RIGOL,DS1054Z,...

    # Configure channel 1
    scope.set_channel_coupling(1, "DC")
    scope.set_channel_scale(1, 0.5)    # 500 mV/div
    scope.set_channel_probe(1, 10.0)   # 10x probe

    # Set timebase: 1 ms/div
    scope.set_timebase_scale(1e-3)

    # Edge trigger
    scope.set_trigger("CHANnel1", 1.0, "POSITIVE")
    scope.set_trigger_sweep("AUTO")

    # Auto-scale and acquire
    scope.auto_scale()
    scope.single()
    scope.wait_ready()

    # Read calibrated waveform
    result = scope.get_waveform(1)
    time_arr, volt_arr = result.value
    print(f"{len(volt_arr)} points, {min(volt_arr):.3f} to {max(volt_arr):.3f} V")
```

## Waveform Readout Details

The `get_waveform(channel)` method performs the following:

1. Sets `:WAVeform:SOURce` to the requested channel
2. Configures WORD format (unsigned, LSB-first)
3. Queries `:WAVeform:PREamble?` for scaling parameters
4. Fetches `:WAVeform:DATA?` via binary transfer
5. Converts raw ADC codes: `V = (raw - yref) * yinc + yor`
6. Generates a time axis: `t = (n - xref) * xinc + xor`

The result is returned as a `MeasurementResult` containing a tuple of
numpy arrays `(time, voltage)`.

### Accessing Individual Scaling Parameters

```python
preamble = scope.get_waveform_preamble()
print(f"Y increment: {preamble['y_increment']} V/code")
print(f"Y origin:    {preamble['y_origin']} V")
print(f"Y reference: {preamble['y_reference']} code")
print(f"X increment: {preamble['x_increment']} s/sample")

# Or query individually:
y_inc = scope.get_waveform_y_increment()
y_ori = scope.get_waveform_y_origin()
x_inc = scope.get_waveform_x_increment()
```

## Channel Configuration

All four channels are independently configurable:

```python
for ch in range(1, 5):
    scope.set_channel_display(ch, ch == 1)   # show only ch1
    scope.set_channel_coupling(ch, "DC")
    scope.set_channel_scale(ch, 1.0)         # 1 V/div
    scope.set_channel_offset(ch, 0.0)
    scope.set_channel_probe(ch, 10.0)
    scope.set_channel_bw_limit(ch, "OFF")    # full bandwidth
    scope.set_channel_invert(ch, False)
    scope.set_channel_units(ch, "VOLTage")
```

## Acquisition Modes

```python
scope.set_acquire_type("HRESolution")   # high-resolution averaging
scope.set_acquire_type("NORMAL")
scope.set_acquire_type("PEAK")          # peak detect
scope.set_acquire_type("AVERages")
scope.set_acquire_averages(64)          # 2^6 = 64 averages
scope.set_acquire_memory_depth(14000000) # 14M points

rate = scope.get_sample_rate()          # 1 GSa/s on DS1054Z
```

## Trigger Configuration

```python
# Edge trigger
scope.safe_send(":TRIGger:MODE EDGE")
scope.set_edge_trigger_source("CHANnel1")
scope.set_edge_trigger_slope("POSitive")
scope.set_edge_trigger_level(1.5)
scope.set_trigger_sweep("NORMal")

# Query trigger status
status = scope.get_trigger_status()  # "TD", "WAIT", "AUTO", etc.
```

## Measurement Helpers

```python
freq = scope.measure_frequency(1)       # :MEASure:FREQuency? CHANnel1
duty = scope.measure_duty_cycle(1)
vpp  = scope.measure_v_peak_to_peak(1)
```

## Screenshot Capture

```python
png_data = scope.get_screenshot()
with open("scope_capture.png", "wb") as f:
    f.write(png_data)
```

## Simulation Mode

The DS1054Z driver does not have a dedicated simulated driver, but the
generic `SimulatedOscilloscope` is used when `INSTRUMATION_MODE=SIM`:

```bash
export INSTRUMATION_MODE=SIM
python my_scope_script.py
```

## Test Coverage

52 unit tests cover:
- Connection, context manager, identity
- Channel config set/get round-trips for all 8 parameters
- Timebase scale/offset
- Acquisition type, averages, memory depth, sample rate
- Edge trigger source/slope/level, sweep mode, status
- Waveform preamble parsing (10-field Rigol format)
- Raw binary data fetch
- Calibrated voltage conversion (`V = (raw - yref) * yinc + yor`)
- Time axis generation
- X/Y increment/origin/reference queries
- Measurement helpers (frequency, duty cycle, Vpp)
- Input validation and boundary checks
