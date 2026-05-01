# Example: Parallel Measurements (Async)

One of the most powerful features of Instrumation is the ability to talk to multiple instruments at once using `asyncio`. This is especially useful for reducing total test time in complex ATE systems.

## Goal
Compare the time taken for sequential measurements against parallel measurements using three simulated instruments.

## The Script
```python
import asyncio
import time
from instrumation.factory import get_instrument

async def run_parallel_demo():
    print("Connecting to simulated instruments...")
    dmm = get_instrument("DMM_ADDR", "DMM")
    sa = get_instrument("SA_ADDR", "SA")
    psu = get_instrument("PSU_ADDR", "PSU")
    
    # Increase simulated latency to make the parallel effect more obvious
    dmm.latency = 0.5
    sa.latency = 0.5
    psu.latency = 0.5
    
    print("\n--- Sequential Measurements ---")
    start = time.perf_counter()
    v = dmm.measure_voltage()
    p = sa.get_peak_value()
    i = psu.get_current()
    end = time.perf_counter()
    print(f"Sequential took: {end - start:.2f} seconds")
    print(f"Results: {v.value:.2f}V, {p.value:.2f}dBm, {i.value:.2f}A")
    
    print("\n--- Parallel Measurements ---")
    start = time.perf_counter()
    # Use the async_ prefix to automatically run commands in background threads
    results = await asyncio.gather(
        dmm.async_measure_voltage(),
        sa.async_get_peak_value(),
        psu.async_get_current()
    )
    end = time.perf_counter()
    v_async, p_async, i_async = results
    print(f"Parallel took: {end - start:.2f} seconds")
    print(f"Results: {v_async.value:.2f}V, {p_async.value:.2f}dBm, {i_async.value:.2f}A")
    
    dmm.close()
    sa.close()
    psu.close()

if __name__ == "__main__":
    # Ensure INSTRUMATION_MODE=SIM to see the timing results correctly
    asyncio.run(run_parallel_demo())
```

## Performance Note
For instruments using Ethernet/TCPIP, this is truly non-blocking. For GPIB/USB, Instrumation uses a background thread pool to ensure your main async loop doesn't stall. In this demo, you'll see the total time drop from ~1.5s (sequential) to ~0.5s (parallel).
