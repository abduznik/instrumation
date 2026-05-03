# Experiment: Keysight MXG N5183B Validation

This document summarizes the validation of the Keysight MXG N5183B Signal Generator.

## Setup
The MXG was connected via LAN (HiSLIP).

## Validation Script
The following script was used to test sweeps and modulation.

```python
def run_advanced_session():
    address = "AUTO"
    with get_instrument(address, "SG") as sg:
        sg.preset()
        sg.set_frequency(2.4e9)
        sg.set_amplitude(-10)
        sg.set_mod_state("PULM", True)
        sg.start_sweep(1e9, 2e9, 11, 0.1)
        sg.check_errors()
```

## Results
The "AUTO" address resolution logic successfully prioritized the HiSLIP interface over the local debug console.

### Recording Snippet (`mxg_session.json`)
The session was captured for "Digital Twin" simulation.
```json
[
  {
    "cmd": "*IDN?",
    "res": "Agilent Technologies, N5183B, MY62221294, B.01.96",
    "ts": 1714711000.0
  },
  {
    "cmd": ":FREQ 2.4 GHz",
    "res": "",
    "ts": 1714711001.0
  }
]
```

## Replay Mode
The recording was verified using the `ReplayDriver`:
```bash
python3 sg_advanced_test.py replay://mxg_session.json
```
**Result**: The test flow was perfectly replayed without the physical instrument, confirming our Golden Master implementation.
