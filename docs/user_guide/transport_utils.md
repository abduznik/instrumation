# Transport Utilities

Instrumation v0.6.0 introduces a set of transport utility functions that help with common instrument communication tasks. These functions are available in the `instrumation.transport` module.

## Overview

| Function | Description |
| --- | --- |
| `detect_line_termination()` | Auto-detect the correct line termination character for an instrument |
| `find_minimum_timeout()` | Find the smallest safe timeout value for an instrument |
| `poll_for_mav()` | Poll the Status Byte Register for the MAV (Message Available) bit |
| `poll_opc_with_backoff()` | Poll for operation-complete with exponential backoff |

## detect_line_termination()

Different instruments use different line-termination characters (LF, CR, or CRLF). When connecting to a new instrument, guessing the wrong terminator causes silent failures. This function automates detection.

```python
import os
os.environ["INSTRUMATION_MODE"] = "SIM"
from instrumation.factory import get_instrument
from instrumation.transport import detect_line_termination

dmm = get_instrument("DUMMY", "DMM")
dmm.connect()
terminator = detect_line_termination(dmm)
print(f"Instrument uses: {repr(terminator)}")
dmm.disconnect()
```

**Returns:** One of `"\n"`, `"\r"`, or `"\r\n"`.

**Raises:** `RuntimeError` if no terminator produces a valid response.

## find_minimum_timeout()

Instruments vary wildly in response time. Setting a timeout too low causes spurious failures; setting it too high makes error detection sluggish. This function finds the smallest timeout that actually works.

```python
import os
os.environ["INSTRUMATION_MODE"] = "SIM"
from instrumation.factory import get_instrument
from instrumation.transport import find_minimum_timeout

dmm = get_instrument("DUMMY", "DMM")
dmm.connect()
min_timeout = find_minimum_timeout(dmm)
print(f"Minimum safe timeout: {min_timeout}ms")
dmm.disconnect()
```

**Returns:** An integer representing milliseconds.

**Raises:** `RuntimeError` if no candidate timeout works.

**Default candidates:** `[100, 250, 500, 1000, 2500, 5000]`

## poll_for_mav()

Many drivers read immediately after a query, but some instruments aren't ready yet. The MAV (Message Available) bit in the Status Byte Register tells you definitively when data is ready.

```python
import os
os.environ["INSTRUMATION_MODE"] = "SIM"
from instrumation.factory import get_instrument
from instrumation.transport import poll_for_mav

dmm = get_instrument("DUMMY", "DMM")
dmm.connect()
poll_for_mav(dmm, timeout=5.0, poll_interval=0.1)
# Now safe to read
dmm.disconnect()
```

**Parameters:**
- `timeout`: Maximum seconds to wait for MAV (default: 10.0)
- `poll_interval`: Seconds between polls (default: 0.1)

**Raises:** `InstrumentTimeout` if MAV is not set within the timeout.

## poll_opc_with_backoff()

Long instrument operations (VNA presets, full calibrations) can take seconds. Polling `*OPC?` at a fixed interval wastes bus traffic. Exponential backoff starts fast (catches quick completions) then backs off to reduce bus load.

```python
import os
os.environ["INSTRUMATION_MODE"] = "SIM"
from instrumation.factory import get_instrument
from instrumation.transport import poll_opc_with_backoff

vna = get_instrument("DUMMY_VNA", "NA")
vna.connect()
vna.preset()
poll_opc_with_backoff(vna, timeout=30.0, initial_delay=0.1, max_delay=2.0)
print("VNA preset complete")
vna.disconnect()
```

**Parameters:**
- `timeout`: Maximum seconds to wait (default: 30.0)
- `initial_delay`: Starting poll delay in seconds (default: 0.1)
- `max_delay`: Maximum delay between polls (default: 1.0)

**Raises:** `InstrumentTimeout` if `*OPC?` does not return "1" within the timeout.

## Scanner Utilities

### find_duplicate_addresses()

On shared buses (GPIB, RS-485), two instruments configured with the same address corrupt each other's responses. This function flags addresses that show up multiple times in a scan result with differing descriptions.

```python
from instrumation.scanner import scan, find_duplicate_addresses

devices = scan()
conflicts = find_duplicate_addresses(devices)
for c in conflicts:
    print(f"CONFLICT on {c['address']}: {c['identities']}")
```

**Returns:** A list of dicts, each with keys:
- `"address"`: The duplicated address string
- `"identities"`: List of distinct descriptions seen
- `"count"`: How many times it appeared

**Returns empty list** if no conflicts found.
