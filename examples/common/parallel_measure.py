import asyncio
import time
import os
import sys

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from instrumation.factory import get_instrument

async def main():
    """
    Demonstrates parallel instrument interrogation using asyncio.
    """
    print("Connecting to instruments (AUTO)...")
    dmm = get_instrument("AUTO", "DMM")
    sa = get_instrument("AUTO", "SA")
    psu = get_instrument("AUTO", "PSU")
    
    dmm.connect()
    sa.connect()
    psu.connect()
    
    if os.environ.get("INSTRUMATION_MODE") == "SIM":
        dmm.latency = 0.5
        sa.latency = 0.5
        psu.latency = 0.5
    
    print("\n--- Sequential Measurements ---")
    start = time.perf_counter()
    v = dmm.measure_voltage()
    sa.peak_search()
    p = sa.get_marker_amplitude()
    i = psu.get_current()
    end = time.perf_counter()
    print(f"Sequential took: {end - start:.2f} seconds")
    print(f"Results: {v.value:.2f}{v.unit}, {p.value:.2f}{p.unit}, {i.value:.2f}{i.unit}")
    
    print("\n--- Parallel Measurements ---")
    start = time.perf_counter()
    sa.peak_search() 
    
    results = await asyncio.gather(
        dmm.async_measure_voltage(),
        sa.async_get_marker_amplitude(),
        psu.async_get_current()
    )
    end = time.perf_counter()
    v_async, p_async, i_async = results
    print(f"Parallel took: {end - start:.2f} seconds")
    print(f"Results: {v_async.value:.2f}{v_async.unit}, {p_async.value:.2f}{p_async.unit}, {i_async.value:.2f}{i_async.unit}")

    dmm.disconnect()
    sa.disconnect()
    psu.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
