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

    def test_simulated_multimeter_measure_temperature(self):
        """Base SimulatedMultimeter should expose measure_temperature.

        The factory returns SimulatedMultimeter (not the Keysight subclass)
        when no specific model is requested, so the base class needs the
        method too — otherwise SIM_DMM crashes with AttributeError.
        """
        from instrumation.drivers.simulated import SimulatedMultimeter
        dmm = SimulatedMultimeter("SIM::DMM")
        t = dmm.measure_temperature()
        self.assertIsInstance(t, MeasurementResult)
        self.assertEqual(t.value, 23.5)
        self.assertEqual(t.unit, "C")

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


    def test_simulated_powersupply_measure_power_realistic(self):
        """Issue #83: SimulatedPowerSupply.measure_power returns voltage * 0.5."""
        from instrumation.drivers.simulated import SimulatedPowerSupply
        psu = SimulatedPowerSupply("USB::SIM::PSU", latency=0)
        psu.connect()

        # Default voltage is 0 -> power should be 0
        p = psu.measure_power()
        self.assertEqual(p.value, 0.0)
        self.assertEqual(p.unit, "W")

        # Set voltage to 5V -> power should be 5 * 0.5 = 2.5W
        psu.set_voltage(5.0)
        p = psu.measure_power()
        self.assertEqual(p.value, 2.5)
        self.assertEqual(p.unit, "W")

        # Set voltage to 12V -> power should be 12 * 0.5 = 6.0W
        psu.set_voltage(12.0)
        p = psu.measure_power()
        self.assertEqual(p.value, 6.0)
        self.assertEqual(p.unit, "W")

        psu.disconnect()

    def test_simulated_powersupply_protection_stubs(self):
        """Issue #82: Verify set_ovp/set_ocp/clear_protection don't crash on SimulatedPowerSupply."""
        from instrumation.drivers.simulated import SimulatedPowerSupply
        psu = SimulatedPowerSupply("USB::SIM::PSU", latency=0)
        psu.connect()

        # These should not raise any exceptions
        psu.set_ovp(30.0)
        psu.set_ocp(5.0)
        psu.clear_protection()

        psu.disconnect()

    def test_simulated_powersupply_foldback_and_autostart_stubs(self):
        """Issue #101: verify foldback/autostart state is tracked in SimulatedPowerSupply."""
        from instrumation.drivers.simulated import SimulatedPowerSupply
        psu = SimulatedPowerSupply("USB::SIM::PSU", latency=0)
        psu.connect()

        self.assertEqual(psu._foldback_mode, "OFF")
        self.assertEqual(psu._foldback_delay, 0.0)
        self.assertFalse(psu._autostart)

        psu.set_foldback_mode("CC")
        psu.set_foldback_delay(2.5)
        psu.set_autostart(True)

        self.assertEqual(psu._foldback_mode, "CC")
        self.assertEqual(psu._foldback_delay, 2.5)
        self.assertTrue(psu._autostart)

        psu.set_foldback_mode("CV")
        self.assertEqual(psu._foldback_mode, "CV")

        psu.set_autostart(False)
        self.assertFalse(psu._autostart)

        psu.disconnect()

    def test_simulated_scope_set_trigger_stub(self):
        """Issue #84: Verify set_trigger doesn't crash on SimulatedOscilloscope."""
        from instrumation.drivers.simulated import SimulatedOscilloscope
        scope = SimulatedOscilloscope("USB::SIM::SCOPE", latency=0)
        scope.connect()

        # Should not raise
        scope.set_trigger("CH1", 0.5, "RISING")
        scope.set_trigger("CH2", -1.0, "FALLING")

        scope.disconnect()

    def test_simulated_vna_marker_stubs(self):
        """Issue #85: Verify peak_search/get_marker_x/get_marker_y don't crash on SimulatedNetworkAnalyzer."""
        from instrumation.drivers.simulated import SimulatedNetworkAnalyzer
        vna = SimulatedNetworkAnalyzer("USB::SIM::VNA", latency=0)
        vna.connect()

        # Should not raise
        vna.peak_search()
        vna.peak_search(marker=2)

        x = vna.get_marker_x()
        self.assertEqual(x, 2.4e9)

        y = vna.get_marker_y()
        self.assertEqual(y, -10.0)

        # Test with explicit marker number
        x2 = vna.get_marker_x(marker=2)
        self.assertEqual(x2, 2.4e9)

        y2 = vna.get_marker_y(marker=3)
        self.assertEqual(y2, -10.0)

        vna.disconnect()


    def test_simulated_scope_channel_aware_measurements(self):
        """Issue #87: Oscilloscope channel-aware measure_frequency/duty_cycle/vpp."""
        from instrumation.drivers.simulated import SimulatedOscilloscope
        scope = SimulatedOscilloscope("USB::SIM::SCOPE", latency=0)
        scope.connect()

        # Default channel (1)
        f = scope.measure_frequency()
        self.assertEqual(f.value, 1000.0)
        self.assertEqual(f.unit, "Hz")

        d = scope.measure_duty_cycle()
        self.assertEqual(d.value, 50.0)
        self.assertEqual(d.unit, "%")

        v = scope.measure_v_peak_to_peak()
        self.assertEqual(v.value, 2.0)
        self.assertEqual(v.unit, "V")

        # Explicit channel
        f2 = scope.measure_frequency(channel=2)
        self.assertEqual(f2.value, 1000.0)
        self.assertEqual(f2.unit, "Hz")

        scope.disconnect()

    def test_simulated_multimeter_configure_voltage_stubs(self):
        """Issue #103: Verify configure_voltage_dc/ac print stubs on SimulatedMultimeter."""
        import io
        import sys
        from instrumation.drivers.simulated import SimulatedMultimeter

        dmm = SimulatedMultimeter("USB::SIM::DMM", latency=0)
        dmm.connect()

        captured_output = io.StringIO()
        sys.stdout = captured_output
        try:
            dmm.configure_voltage_dc()
            dmm.configure_voltage_ac()
        finally:
            sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertIn("[SIM] DMM Configured: DC Voltage", output)
        self.assertIn("[SIM] DMM Configured: AC Voltage", output)

        dmm.disconnect()

    def test_simulated_keysight34461a_configure_voltage_stubs(self):
        """Issue #103: Verify configure_voltage_dc/ac print stubs on SimulatedKeysight34461A."""
        import io
        import sys
        from instrumation.drivers.simulated import SimulatedKeysight34461A

        dmm = SimulatedKeysight34461A("USB::SIM::34461A")
        dmm.connect()

        captured_output = io.StringIO()
        sys.stdout = captured_output
        try:
            dmm.configure_voltage_dc()
            dmm.configure_voltage_ac()
        finally:
            sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertIn("[SIM] 34461A Configured: DC Voltage", output)
        self.assertIn("[SIM] 34461A Configured: AC Voltage", output)

        dmm.disconnect()

    def test_anritsu_sa_driver_interface(self):
        """Issue #102: Verify AnritsuSA driver implements SpectrumAnalyzer interface."""
        from instrumation.drivers.anritsu import AnritsuSA
        from instrumation.drivers.base import SpectrumAnalyzer

        self.assertTrue(issubclass(AnritsuSA, SpectrumAnalyzer))
        self.assertTrue(hasattr(AnritsuSA, 'preset'))
        self.assertTrue(hasattr(AnritsuSA, 'peak_search'))
        self.assertTrue(hasattr(AnritsuSA, 'get_marker_amplitude'))
        self.assertTrue(hasattr(AnritsuSA, 'set_center_freq'))
        self.assertTrue(hasattr(AnritsuSA, 'get_center_freq'))
        self.assertTrue(hasattr(AnritsuSA, 'set_span'))
        self.assertTrue(hasattr(AnritsuSA, 'get_span'))
        self.assertTrue(hasattr(AnritsuSA, 'set_ref_level'))
        self.assertTrue(hasattr(AnritsuSA, 'set_attenuation'))
        self.assertTrue(hasattr(AnritsuSA, 'set_rbw'))
        self.assertTrue(hasattr(AnritsuSA, 'set_vbw'))
        self.assertTrue(hasattr(AnritsuSA, 'get_trace_data'))
        self.assertTrue(hasattr(AnritsuSA, 'shutdown_safety'))

    def test_anritsu_vna_driver_interface(self):
        """Issue #102: Verify AnritsuVNA driver implements NetworkAnalyzer interface."""
        from instrumation.drivers.anritsu import AnritsuVNA
        from instrumation.drivers.base import NetworkAnalyzer

        self.assertTrue(issubclass(AnritsuVNA, NetworkAnalyzer))
        self.assertTrue(hasattr(AnritsuVNA, 'preset'))
        self.assertTrue(hasattr(AnritsuVNA, 'set_start_frequency'))
        self.assertTrue(hasattr(AnritsuVNA, 'set_stop_frequency'))
        self.assertTrue(hasattr(AnritsuVNA, 'set_points'))
        self.assertTrue(hasattr(AnritsuVNA, 'set_parameter'))
        self.assertTrue(hasattr(AnritsuVNA, 'get_trace_data'))
        self.assertTrue(hasattr(AnritsuVNA, 'get_complex_trace'))
        self.assertTrue(hasattr(AnritsuVNA, 'get_smith_data'))

    def test_anritsu_shockline_vna_driver_interface(self):
        """Issue #102: Verify AnritsuShockLineVNA driver implements NetworkAnalyzer interface."""
        from instrumation.drivers.anritsu import AnritsuShockLineVNA
        from instrumation.drivers.base import NetworkAnalyzer

        self.assertTrue(issubclass(AnritsuShockLineVNA, NetworkAnalyzer))
        self.assertTrue(hasattr(AnritsuShockLineVNA, 'preset'))
        self.assertTrue(hasattr(AnritsuShockLineVNA, 'set_start_frequency'))
        self.assertTrue(hasattr(AnritsuShockLineVNA, 'set_stop_frequency'))
        self.assertTrue(hasattr(AnritsuShockLineVNA, 'set_points'))
        self.assertTrue(hasattr(AnritsuShockLineVNA, 'set_if_bandwidth'))
        self.assertTrue(hasattr(AnritsuShockLineVNA, 'set_parameter'))
        self.assertTrue(hasattr(AnritsuShockLineVNA, 'get_trace_data'))
        self.assertTrue(hasattr(AnritsuShockLineVNA, 'get_complex_trace'))
        self.assertTrue(hasattr(AnritsuShockLineVNA, 'get_smith_data'))
        self.assertTrue(hasattr(AnritsuShockLineVNA, 'shutdown_safety'))

    def test_anritsu_ms2035b_combo_driver_interface(self):
        """Issue #102: Verify AnritsuMS2035B driver implements both SA and VNA interfaces."""
        from instrumation.drivers.anritsu import AnritsuMS2035B
        from instrumation.drivers.base import SpectrumAnalyzer, NetworkAnalyzer

        self.assertTrue(issubclass(AnritsuMS2035B, SpectrumAnalyzer))
        self.assertTrue(issubclass(AnritsuMS2035B, NetworkAnalyzer))

        # SA methods
        self.assertTrue(hasattr(AnritsuMS2035B, 'set_center_freq'))
        self.assertTrue(hasattr(AnritsuMS2035B, 'get_center_freq'))
        self.assertTrue(hasattr(AnritsuMS2035B, 'set_span'))
        self.assertTrue(hasattr(AnritsuMS2035B, 'get_span'))
        self.assertTrue(hasattr(AnritsuMS2035B, 'get_trace_data'))

        # VNA methods
        self.assertTrue(hasattr(AnritsuMS2035B, 'set_start_frequency'))
        self.assertTrue(hasattr(AnritsuMS2035B, 'set_stop_frequency'))
        self.assertTrue(hasattr(AnritsuMS2035B, 'set_points'))
        self.assertTrue(hasattr(AnritsuMS2035B, 'set_parameter'))
        self.assertTrue(hasattr(AnritsuMS2035B, 'get_complex_trace'))
        self.assertTrue(hasattr(AnritsuMS2035B, 'get_smith_data'))

    def test_anritsu_driver_registration(self):
        """Issue #102: Verify Anritsu drivers are registered in the driver registry."""
        from instrumation.factory import load_plugins
        from instrumation.drivers.registry import DriverRegistry

        # Load all drivers (including Anritsu)
        load_plugins()

        # AnritsuSA should be registered as SA
        sa_drivers = DriverRegistry.get_drivers_by_type("SA")
        anritsu_sa_registered = any(
            "AnritsuSA" in cls.__name__ for cls in sa_drivers
        )
        self.assertTrue(anritsu_sa_registered, "AnritsuSA should be registered as SA driver")

        # AnritsuVNA and AnritsuShockLineVNA should be registered as NA
        na_drivers = DriverRegistry.get_drivers_by_type("NA")
        anritsu_vna_registered = any(
            "AnritsuVNA" in cls.__name__ for cls in na_drivers
        )
        anritsu_shockline_registered = any(
            "AnritsuShockLineVNA" in cls.__name__ for cls in na_drivers
        )
        self.assertTrue(anritsu_vna_registered, "AnritsuVNA should be registered as NA driver")
        self.assertTrue(anritsu_shockline_registered, "AnritsuShockLineVNA should be registered as NA driver")

        # AnritsuMS2035B should be registered as COMBO_VNA_SA
        combo_drivers = DriverRegistry.get_drivers_by_type("COMBO_VNA_SA")
        anritsu_combo_registered = any(
            "AnritsuMS2035B" in cls.__name__ for cls in combo_drivers
        )
        self.assertTrue(anritsu_combo_registered, "AnritsuMS2035B should be registered as COMBO_VNA_SA driver")


if __name__ == "__main__":
    unittest.main()
