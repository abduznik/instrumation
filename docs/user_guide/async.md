# Asynchronous Measurements

Instrumation provides built-in support for `asyncio`, allowing you to take measurements from multiple instruments simultaneously without blocking.

## Basic Usage
Every measurement method has an `async_` counterpart.

```python
import asyncio
from instrumation.factory import get_instrument

async def main():
    dmm = get_instrument("ADDR1", "DMM")
    sa = get_instrument("ADDR2", "SA")
    
    # Measure in parallel
    results = await asyncio.gather(
        dmm.async_measure_voltage(),
        sa.async_get_peak_value()
    )
    
    print(f"Voltage: {results[0].value}")
    print(f"Power: {results[1].value}")

asyncio.run(main())
```

## How it works
For real hardware drivers that use blocking VISA calls, Instrumation automatically offloads the work to a thread pool using `asyncio.to_thread`.
