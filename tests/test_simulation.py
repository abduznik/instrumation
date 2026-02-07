import unittest
import os
from instrumation.factory import get_instrument

class TestSimulation(unittest.TestCase):
    def setUp(self):
        # Ensure we are in SIM mode for these tests
        os.environ["INSTRUMATION_MODE"] = "SIM"

    def test_connection(self):
        """Assert that the driver returned is indeed a simulation."""
        # We request a Multimeter (DMM)
        driver = get_instrument("USB::0x1234::SIM", "DMM")
        driver.connect()
        
        dev_id = driver.get_id()
        driver.disconnect()
        
        self.assertTrue("SIM" in dev_id or "SIMULATED" in dev_id)

    def test_physics(self):
        """Assert that the simulation returns valid physical data (float > 0)."""
        driver = get_instrument("USB::0x1234::SIM", "DMM")
        driver.connect()
        
        # Measure voltage (Simulated DMM creates ~5.0V with noise)
        voltage = driver.measure_voltage()
        
        driver.disconnect()
        
        self.assertIsInstance(voltage, float)
        self.assertGreater(voltage, 0.0)

if __name__ == "__main__":
    unittest.main()