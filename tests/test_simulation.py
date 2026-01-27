import pytest
import os
from instrumation.factory import get_instrument

# Ensure we are in SIM mode for these tests
os.environ["INSTRUMATION_MODE"] = "SIM"

def test_connection():
    """Assert that the driver returned is indeed a simulation."""
    # We request a Multimeter (DMM)
    driver = get_instrument("USB::0x1234::SIM", "DMM")
    driver.connect()
    
    dev_id = driver.get_id()
    driver.disconnect()
    
    assert "SIM" in dev_id or "SIMULATED" in dev_id

def test_physics():
    """Assert that the simulation returns valid physical data (float > 0)."""
    driver = get_instrument("USB::0x1234::SIM", "DMM")
    driver.connect()
    
    # Measure voltage (Simulated DMM creates ~5.0V with noise)
    voltage = driver.measure_voltage()
    
    driver.disconnect()
    
    assert isinstance(voltage, float)
    assert voltage > 0.0
