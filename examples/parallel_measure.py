import asyncio
import time
from instrumation.factory import get_instrument

async def run_parallel_demo():
    print("Connecting to simulated instruments...")
    dmm = get_instrument("DMM_ADDR", "DMM")
    sa = get_instrument("SA_ADDR", "SA")
    psu = get_instrument("PSU_ADDR", "PSU")
    
    # Increase latency to make the parallel effect more obvious
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
    results = await asyncio.gather(
        dmm.async_measure_voltage(),
        sa.async_get_peak_value(),
        psu.async_get_current()
    )
    end = time.perf_counter()
    v_async, p_async, i_async = results
    print(f"Parallel took: {end - start:.2f} seconds")
    print(f"Results: {v_async.value:.2f}V, {p_async.value:.2f}dBm, {i_async.value:.2f}A")

if __name__ == "__main__":
    asyncio.run(run_parallel_demo())
