import pytest
import asyncio
import time
import os
from instrumation.factory import get_instrument

@pytest.mark.asyncio
async def test_async_measurements():
    """Test that async measurements work and don't block each other."""
    os.environ["INSTRUMATION_MODE"] = "SIM"
    
    dmm = get_instrument("DMM_ADDR", "DMM")
    psu = get_instrument("PSU_ADDR", "PSU")
    
    # Set latency to 0.2s for each
    dmm.latency = 0.2
    psu.latency = 0.2
    
    start = time.perf_counter()
    results = await asyncio.gather(
        dmm.async_measure_voltage(),
        psu.async_get_current()
    )
    end = time.perf_counter()
    
    duration = end - start
    # Should take around 0.2s (parallel), not 0.4s (sequential)
    assert 0.15 < duration < 0.35
    assert results[0].value > 0
    assert results[1].value == 0.0

@pytest.mark.asyncio
async def test_async_spectrum_analyzer():
    """Test async SA peak search + amplitude."""
    os.environ["INSTRUMATION_MODE"] = "SIM"
    sa = get_instrument("SA_ADDR", "SA")
    sa.latency = 0.1
    
    await sa.set_center_freq(1.5e9)
    res = await sa.async_get_peak_value()
    assert res.unit == "dBm"
    assert -25 < res.value < -15
