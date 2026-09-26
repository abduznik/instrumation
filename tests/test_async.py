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
    
    await sa.async_set_center_freq(1.5e9)
    res = await sa.async_get_marker_amplitude()
    assert res.unit == "dBm"
    assert -25 < res.value < -15


@pytest.mark.asyncio
async def test_wrap_async_forwards_kwargs():
    """GH #244: async wrappers must forward kwargs such as channel=."""
    from unittest.mock import MagicMock
    from instrumation.drivers.async_driver import wrap_async
    from instrumation.drivers.rigol_psu import RigolDP832

    psu = RigolDP832("TCPIP::1::INSTR")
    psu.inst = MagicMock()
    psu.check_errors_enabled = False
    await wrap_async(psu).set_voltage(3.3, channel=2)
    psu.inst.write.assert_called_with("SOUR2:VOLT 3.3")
