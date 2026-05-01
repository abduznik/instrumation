# Example: Parallel Measurements (Async)

One of the most powerful features of Instrumation is the ability to talk to multiple instruments at once using `asyncio`.

## Goal
Measure the input voltage from a DMM and the output signal peak from a Spectrum Analyzer at the same time to calculate gain.

## The Script
```python
import asyncio
from instrumation.factory import get_instrument

async def gain_test():
    # 1. Connect to both instruments
    # In a real lab, replace these with actual VISA addresses
    dmm = get_instrument("AUTO", "DMM")
    sa = get_instrument("AUTO", "SA")
    
    print("Starting parallel measurement...")
    
    # 2. Run both commands at the same time
    # This saves time by avoiding sequential execution
    voltage_task = dmm.async_measure_voltage()
    power_task = sa.async_get_peak_value()
    
    v_res, p_res = await asyncio.gather(voltage_task, power_task)
    
    # 3. Calculate and display results
    print(f"Input: {v_res.value} V")
    print(f"Output: {p_res.value} dBm")
    
    # Context management is handled manually here or using async with
    dmm.close()
    sa.close()

if __name__ == "__main__":
    asyncio.run(gain_test())
```

## Performance Note
For instruments using Ethernet/TCPIP, this is truly non-blocking. For GPIB/USB, Instrumation uses a background thread pool to ensure your main async loop doesn't stall.
