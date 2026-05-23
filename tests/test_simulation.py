import unittest
import os
from instrumation.factory import get_instrument
from instrumation.results import MeasurementResult

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
        
        self.assertGreater(voltage.value, 0.0)

    def test_oscilloscope(self):
        """Assert that the simulated oscilloscope returns valid waveforms and measurements."""
        driver = get_instrument("USB::0x1234::SIM", "SCOPE")
        if driver is None:
            self.fail("get_instrument returned None for 'SCOPE'")
            
        driver.connect()
        
        # 1. Waveform acquisition
        waveform_res = driver.get_waveform(1)
        waveform = waveform_res.value
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
        self.assertAlmostEqual(freq.value, 1000.0, delta=200.0) # 1kHz +/- noise
        
        # Vpp should be around 2.0V based on driver implementation
        self.assertAlmostEqual(vpp.value, 2.0, delta=0.5) 
        
        driver.disconnect()

    def test_simulated_keithley2400_smu(self):
        """Digital Twin: Simulated Keithley 2400 SMU."""
        from instrumation.drivers.simulated import SimulatedKeithley2400
        smu = SimulatedKeithley2400("USB::SIM::2400")
        smu.connect()

        # Test sourcing
        smu.set_voltage(5.0)
        self.assertEqual(smu.get_voltage(), 5.0)

        smu.set_output(True)
        self.assertTrue(smu.get_output())

        # Test measurement
        v = smu.measure_voltage()
        self.assertIsInstance(v.value, float)
        self.assertEqual(v.unit, "V")

        i = smu.measure_current()
        self.assertIsInstance(i.value, float)
        self.assertEqual(i.unit, "A")

        r = smu.measure_resistance()
        self.assertIsInstance(r.value, float)
        self.assertEqual(r.unit, "Ohm")

        p = smu.measure_power()
        self.assertIsInstance(p.value, float)
        self.assertEqual(p.unit, "W")

        smu.disconnect()

    def test_simulated_keithley2400_psu_registration(self):
        """Digital Twin: Keithley 2400 should be reachable as PSU."""
        os.environ["INSTRUMATION_MODE"] = "SIM"
        with get_instrument("SIM_PSU", "PSU") as psu:
            self.assertTrue(psu.connected)
            # Should have source capabilities
            psu.set_voltage(12.0)
            psu.set_output(True)

    def test_simulated_keysight34461a_dmm(self):
        """Digital Twin: Simulated Keysight 34461A DMM."""
        from instrumation.drivers.simulated import SimulatedKeysight34461A
        dmm = SimulatedKeysight34461A("USB::SIM::34461A")
        dmm.connect()

        v = dmm.measure_voltage()
        self.assertAlmostEqual(v.value, 4.95, delta=0.1)
        self.assertEqual(v.unit, "V")
        self.assertIsInstance(v, MeasurementResult)

        vac = dmm.measure_voltage(ac=True)
        self.assertAlmostEqual(vac.value, 4.90, delta=0.1)
        self.assertEqual(vac.unit, "V")

        r = dmm.measure_resistance()
        self.assertEqual(r.value, 1000.0)
        self.assertEqual(r.unit, "Ohm")

        i = dmm.measure_current()
        self.assertEqual(i.unit, "A")

        f = dmm.measure_frequency()
        self.assertEqual(f.value, 1000.0)
        self.assertEqual(f.unit, "Hz")

        t = dmm.measure_temperature()
        self.assertEqual(t.value, 23.5)
        self.assertEqual(t.unit, "C")

        c = dmm.measure_capacitance()
        self.assertEqual(c.unit, "F")

        d = dmm.measure_diode()
        self.assertEqual(d.unit, "V")

        dmm.disconnect()

    def test_simulated_keysight34461a_factory_access(self):
        """Digital Twin: Keysight 34461A via factory DMM."""
        os.environ["INSTRUMATION_MODE"] = "SIM"
        with get_instrument("SIM_DMM", "DMM") as dmm:
            self.assertTrue(dmm.connected)
            res = dmm.measure_voltage()
            self.assertIsInstance(res, MeasurementResult)

    def test_simulated_multimeter_capacitance_and_diode(self):
        """Base SimulatedMultimeter should expose measure_capacitance and measure_diode.

        Factory-built SIM_DMM returns SimulatedMultimeter (not the Keysight
        subclass), so the base class needs these methods or any code reading
        a capacitance/diode through the factory crashes with AttributeError.
        """
        from instrumation.drivers.simulated import SimulatedMultimeter
        dmm = SimulatedMultimeter("SIM::DMM")

        c = dmm.measure_capacitance()
        self.assertIsInstance(c, MeasurementResult)
        self.assertEqual(c.value, 10e-6)
        self.assertEqual(c.unit, "F")

        d = dmm.measure_diode()
        self.assertIsInstance(d, MeasurementResult)
        self.assertEqual(d.value, 0.6)
        self.assertEqual(d.unit, "V")


if __name__ == "__main__":
    unittest.main()