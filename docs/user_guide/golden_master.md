# Golden Master (Record & Replay)

The Golden Master feature allows you to record exact SCPI interactions with real hardware and replay them later. This is perfect for debugging complex measurement sequences without occupying a lab station.

## Recording a Session

Use the CLI to record a manual session:

```bash
instrumation record "USB0::0x2A8D::0x0101::MY12345678::0::INSTR" DMM my_dmm_session.json
```

Inside the recording loop, you can enter SCPI commands like `*IDN?` or `MEAS:VOLT?`. When you type `quit`, the session is saved to the JSON file.

## Replaying a Session

To use the recorded data in your Python script:

```python
from instrumation.factory import get_instrument

# Use the replay:// protocol
address = "replay://my_dmm_session.json"
with get_instrument(address, "DMM") as dmm:
    # This will return the exact data recorded previously
    res = dmm.measure_voltage()
    print(f"Replayed: {res.value} {res.unit}")
```
