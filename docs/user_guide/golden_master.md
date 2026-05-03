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

## Programmatic Recording (`RecordingWrapper`)

For complex scripts, you can wrap any real instrument to capture its session automatically:

```python
from instrumation.factory import get_instrument
from instrumation.drivers.replay import RecordingWrapper, GoldenMaster

with get_instrument("AUTO", "SA") as sa:
    # Wrap the instrument to record all SCPI traffic
    gm = GoldenMaster("my_lab_session.json")
    sa = RecordingWrapper(sa, gm)
    
    # Run your test logic
    sa.preset()
    sa.set_center_freq(2.4e9)
    
    # Save the session to disk
    gm.save()
```
