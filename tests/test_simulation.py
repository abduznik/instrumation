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

    def test_oscilloscope(self):
        """Assert that the simulated oscilloscope returns valid waveforms and measurements."""
        driver = get_instrument("USB::0x1234::SIM", "SCOPE")
        if driver is None:
            self.fail("get_instrument returned None for 'SCOPE'")
            
        driver.connect()
        
        # 1. Waveform acquisition
        waveform = driver.get_waveform(1)
        self.assertIsInstance(waveform, list)
        self.assertEqual(len(waveform), 1000)
        
        # Verify waveform data properties (Sine wave simulation)
        # Should have both positive and negative values around the mean
        self.assertTrue(any(v > 0 for v in waveform))
        self.assertTrue(any(v < 0 for v in waveform))

        # 2. Measurements
        freq = driver.measure_frequency()
        vpp = driver.measure_v_peak_to_peak()
        
        # Specific assertions for the simulated 1kHz sine wave
        self.assertIsInstance(freq, float)
        self.assertAlmostEqual(freq, 1000.0, delta=200.0) # 1kHz +/- noise
        
        # Vpp should be around 2.0V based on driver implementation
        self.assertIsInstance(vpp, float)
        self.assertAlmostEqual(vpp, 2.0, delta=0.5) 
        
        driver.disconnect()

if __name__ == "__main__":
    unittest.main()