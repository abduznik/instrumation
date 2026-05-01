# Unified Exception Hierarchy

Instrumation provides a standardized set of exceptions to handle hardware and communication errors gracefully. Instead of catching generic `Exception` or driver-specific errors, you should use the hierarchy defined in `instrumation.exceptions`.

## Available Exceptions

All exceptions inherit from `InstrumentError`.

| Exception | Description |
| --- | --- |
| `InstrumentError` | Base class for all instrument-related errors. |
| `InstrumentTimeout` | Raised when an operation (query/write) times out. |
| `ConnectionLost` | Raised when the connection is dropped or cannot be established. |
| `OverloadError` | Raised when the instrument detects an input overload condition. |
| `ConfigurationError` | Raised when an invalid parameter or command is sent. |

## Usage Example

```python
from instrumation.factory import get_instrument
from instrumation.exceptions import InstrumentTimeout, ConnectionLost

try:
    with get_instrument("TCPIP0::192.168.1.100::INSTR", "DMM") as dmm:
        val = dmm.measure_voltage()
        print(f"Reading: {val}")
except InstrumentTimeout:
    print("The instrument did not respond in time.")
except ConnectionLost:
    print("Lost connection to the instrument. Check your network.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
```

## Why use this?

In large-scale automated test environments, distinguishing between a **timeout** (slow response) and a **connection loss** (physical disconnection) is critical for deciding whether to retry a test or abort the entire station.
