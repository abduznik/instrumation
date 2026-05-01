# Robust Error Handling

This example demonstrates how to use the unified exception hierarchy to create reliable test automation that can recover from minor communication glitches.

## Code

```python
from instrumation.factory import get_instrument
from instrumation.exceptions import InstrumentTimeout, ConnectionLost, InstrumentError

def measure_with_retry(address, retries=3):
    attempt = 0
    while attempt < retries:
        try:
            with get_instrument(address, "DMM") as dmm:
                return dmm.measure_voltage()
        except InstrumentTimeout:
            print(f"Timeout on attempt {attempt+1}. Retrying...")
            attempt += 1
        except ConnectionLost:
            # Fatal error, no point in retrying immediately
            print("Connection lost. Aborting.")
            break
        except InstrumentError as e:
            print(f"Instrument error: {e}. Retrying...")
            attempt += 1
    return None

if __name__ == "__main__":
    res = measure_with_retry("AUTO")
    if res:
        print(f"Final Reading: {res}")
```

## Why this is useful

Real-world RF labs often suffer from EMI (Electromagnetic Interference) or network congestion that can cause a single SCPI command to time out. By catching `InstrumentTimeout` specifically, you can implement retries without masking more serious issues like a `ConnectionLost`.
