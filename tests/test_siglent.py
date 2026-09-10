import unittest
from unittest.mock import MagicMock, patch
from instrumation.drivers.siglent import SiglentSDS
from instrumation import connect_instrument
from instrumation.factory import get_instrument

class TestSiglentSDS(unittest.TestCase):
    def setUp(self):
        self.mock_resource = MagicMock()
        # Mock pyvisa.ResourceManager
        with patch('pyvisa.ResourceManager'):
            self.driver = SiglentSDS("USB0::0x1AB1::0x04CE::SDS1000::INSTR")
            self.driver.inst = self.mock_resource
            self.driver.inst.query.return_value = "1"
            self.driver.connected = True
        
        # Ensure we are NOT in SIM mode for these tests by default
        import os
        self._old_mode = os.environ.get("INSTRUMATION_MODE")
        os.environ["INSTRUMATION_MODE"] = "REAL"

    def tearDown(self):
        import os
        if self._old_mode is None:
            del os.environ["INSTRUMATION_MODE"]
        else:
            os.environ["INSTRUMATION_MODE"] = self._old_mode

    def test_run(self):
        self.driver.run()
        self.mock_resource.write.assert_called_with("ARM")

    def test_stop(self):
        self.driver.stop()
        self.mock_resource.write.assert_called_with("STOP")

    def test_single(self):
        self.driver.single()
        self.mock_resource.write.assert_called_with("SING")

    def test_get_waveform(self):
        # Mocking binary data return with Siglent header
        header = b"C1:WF DAT2,"
        data = bytes([0, 1, 2, 3])
        footer = b"\n\r"
        self.mock_resource.read_raw.return_value = header + data + footer
        
        res = self.driver.get_waveform(1)
        self.assertEqual(res.value, [0.0, 1.0, 2.0, 3.0])
        self.assertEqual(res.unit, "V")

    def test_factory_registration(self):
        # Testing get_instrument for real hardware path
        # Mock RealDriver at the factory level AND the SiglentSDS connect method
        with patch('instrumation.factory.RealDriver') as mock_real, \
             patch('instrumation.drivers.siglent.SiglentSDS.connect'):
            mock_inst = mock_real.return_value
            mock_inst.get_id.return_value = "SIGLENT,SDS1000,1,1"
            
            driver = get_instrument("USB::0x1AB1::0x04CE::INSTR", "SCOPE")
            self.assertIsInstance(driver, SiglentSDS)

    def test_auto_detection(self):
        # Testing connect_instrument auto-detection
        mock_rm = MagicMock()
        mock_res = MagicMock()
        # Ensure IDN identifies it as Siglent so factory routes correctly
        mock_res.query.return_value = "SIGLENT,SDS1202X-E,SDS1EBX2R4567,1.3.9R1"
        
        with patch('instrumation.factory.get_rm', return_value=mock_rm), \
             patch('instrumation.factory.RealDriver') as mock_real:
            mock_real.return_value.get_id.return_value = "SIGLENT,SDS1202X-E,..."
            mock_rm.open_resource.return_value = mock_res
            driver = connect_instrument("USB::SIGLENT::SDS::INSTR")
            self.assertIsInstance(driver, SiglentSDS)
            
class TestSiglentSDSInterface(unittest.TestCase):
    """Issue #110: Interface validation tests for SiglentSDS, following the
    test_anritsu_* pattern in test_simulation.py."""

    def test_siglent_sds_driver_interface(self):
        """Verify SiglentSDS implement Oscilloscope interface."""
        from instrumation.drivers.base import Oscilloscope

        self.assertTrue(issubclass(SiglentSDS, Oscilloscope))
        self.assertTrue(hasattr(SiglentSDS, 'preset'))
        self.assertTrue(hasattr(SiglentSDS, 'run'))
        self.assertTrue(hasattr(SiglentSDS, 'stop'))
        self.assertTrue(hasattr(SiglentSDS, 'single'))
        self.assertTrue(hasattr(SiglentSDS, 'get_waveform'))
        self.assertTrue(hasattr(SiglentSDS, 'auto_scale'))
        self.assertTrue(hasattr(SiglentSDS, 'set_trigger'))
        self.assertTrue(hasattr(SiglentSDS, 'get_screenshot'))
        self.assertTrue(hasattr(SiglentSDS, 'measure_frequency'))
        self.assertTrue(hasattr(SiglentSDS, 'measure_duty_cycle'))
        self.assertTrue(hasattr(SiglentSDS, 'measure_v_peak_to_peak'))
        self.assertTrue(hasattr(SiglentSDS, 'shutdown_safety'))

    def test_siglent_sds_driver_registration(self):
        """Verify SiglentSDS is registered in the driver registry as SCOPE."""
        from instrumation.factory import load_plugins
        from instrumation.drivers.registry import DriverRegistry

        load_plugins()

        scope_drivers = DriverRegistry.get_drivers_by_type("SCOPE")
        siglent_sds_registered = any(
            "SiglentSDS" in cls.__name__ for cls in scope_drivers
        )
        self.assertTrue(siglent_sds_registered, "SiglentSDS should be registered as SCOPE driver")


class TestSiglentSDSEnhanced(unittest.TestCase):
    """GH #177: Tests for comprehensive auto-measurements, channel config,
    and math functions added to SiglentSDS."""

    def setUp(self):
        self.mock_resource = MagicMock()
        with patch('pyvisa.ResourceManager'):
            self.driver = SiglentSDS("USB0::0x1AB1::0x04CE::SDS1000::INSTR")
            self.driver.inst = self.mock_resource
            self.driver.inst.query.return_value = "1"
            self.driver.connected = True

    # ── Auto-Measurements ────────────────────────────────────────

    def test_measure_v_max(self):
        self.mock_resource.query.return_value = "CH1:PAVA VMAX,3.45V"
        res = self.driver.measure_v_max(1)
        self.assertAlmostEqual(res.value, 3.45)
        self.assertEqual(res.unit, "V")

    def test_measure_v_min(self):
        self.mock_resource.query.return_value = "CH1:PAVA VMIN,-1.23V"
        res = self.driver.measure_v_min(1)
        self.assertAlmostEqual(res.value, -1.23)
        self.assertEqual(res.unit, "V")

    def test_measure_v_rms(self):
        self.mock_resource.query.return_value = "CH1:PAVA VRMS,2.10V"
        res = self.driver.measure_v_rms(1)
        self.assertAlmostEqual(res.value, 2.10)
        self.assertEqual(res.unit, "V")

    def test_measure_v_amp(self):
        self.mock_resource.query.return_value = "CH1:PAVA VAMP,4.50V"
        res = self.driver.measure_v_amp(1)
        self.assertAlmostEqual(res.value, 4.50)

    def test_measure_v_base(self):
        self.mock_resource.query.return_value = "CH1:PAVA VBASE,-0.50V"
        res = self.driver.measure_v_base(1)
        self.assertAlmostEqual(res.value, -0.50)

    def test_measure_v_overshoot(self):
        self.mock_resource.query.return_value = "CH1:PAVA VOVS,5.2%"
        res = self.driver.measure_v_overshoot(1)
        self.assertAlmostEqual(res.value, 5.2)
        self.assertEqual(res.unit, "%")

    def test_measure_v_preshoot(self):
        self.mock_resource.query.return_value = "CH1:PAVA VPRE,2.1%"
        res = self.driver.measure_v_preshoot(1)
        self.assertAlmostEqual(res.value, 2.1)

    def test_measure_rise_time(self):
        self.mock_resource.query.return_value = "CH1:PAVA RTIM,1.23e-9s"
        res = self.driver.measure_rise_time(1)
        self.assertAlmostEqual(res.value, 1.23e-9)
        self.assertEqual(res.unit, "s")

    def test_measure_fall_time(self):
        self.mock_resource.query.return_value = "CH1:PAVA FTIM,2.34e-9s"
        res = self.driver.measure_fall_time(1)
        self.assertAlmostEqual(res.value, 2.34e-9)

    def test_measure_period(self):
        self.mock_resource.query.return_value = "CH1:PAVA PERI,1.00e-3s"
        res = self.driver.measure_period(1)
        self.assertAlmostEqual(res.value, 1.00e-3)
        self.assertEqual(res.unit, "s")

    # ── Channel Configuration ─────────────────────────────────────

    def test_set_channel_scale(self):
        self.driver.set_channel_scale(1, 0.5)
        self.mock_resource.write.assert_any_call("C1:SCAL 0.5")

    def test_set_channel_offset(self):
        self.driver.set_channel_offset(2, -1.25)
        self.mock_resource.write.assert_any_call("C2:OFFS -1.25")

    def test_set_channel_coupling_dc(self):
        self.driver.set_channel_coupling(1, "DC")
        self.mock_resource.write.assert_any_call("C1:COUP DC")

    def test_set_channel_coupling_ac(self):
        self.driver.set_channel_coupling(1, "AC")
        self.mock_resource.write.assert_any_call("C1:COUP AC")

    def test_set_channel_coupling_invalid(self):
        with self.assertRaises(ValueError):
            self.driver.set_channel_coupling(1, "INVALID")

    def test_set_channel_probe(self):
        self.driver.set_channel_probe(1, 10)
        self.mock_resource.write.assert_any_call("C1:PROB 10")

    def test_set_channel_state_on(self):
        self.driver.set_channel_state(1, "ON")
        self.mock_resource.write.assert_any_call("C1:TRL ON")

    def test_set_channel_state_off(self):
        self.driver.set_channel_state(3, "OFF")
        self.mock_resource.write.assert_any_call("C3:TRL OFF")

    def test_set_channel_state_invalid(self):
        with self.assertRaises(ValueError):
            self.driver.set_channel_state(1, "MAYBE")

    def test_channel_configure_all(self):
        self.driver.channel_configure(1, scale=1.0, offset=0.5, coupling="DC", probe=10)
        self.mock_resource.write.assert_any_call("C1:SCAL 1.0")
        self.mock_resource.write.assert_any_call("C1:OFFS 0.5")
        self.mock_resource.write.assert_any_call("C1:COUP DC")
        self.mock_resource.write.assert_any_call("C1:PROB 10")

    def test_channel_configure_partial(self):
        self.driver.channel_configure(2, scale=2.0, probe=100)
        self.mock_resource.write.assert_any_call("C2:SCAL 2.0")
        self.mock_resource.write.assert_any_call("C2:PROB 100")
        # Offset and coupling should NOT be called
        calls = [str(c) for c in self.mock_resource.write.call_args_list]
        self.assertFalse(any("C2:OFFS" in c for c in calls))
        self.assertFalse(any("C2:COUP" in c for c in calls))

    # ── Math Functions ────────────────────────────────────────────

    def test_set_math_function_add(self):
        self.driver.set_math_function(1, 2, "ADD")
        self.mock_resource.write.assert_any_call("MATH:AUX:MATH:ADD,C1,C2")

    def test_set_math_function_sub(self):
        self.driver.set_math_function(3, 4, "SUB")
        self.mock_resource.write.assert_any_call("MATH:AUX:MATH:SUB,C3,C4")

    def test_set_math_function_mul(self):
        self.driver.set_math_function(1, 2, "MUL")
        self.mock_resource.write.assert_any_call("MATH:AUX:MATH:MUL,C1,C2")

    def test_set_math_function_inv(self):
        self.driver.set_math_function(1, 1, "INV")
        self.mock_resource.write.assert_any_call("MATH:AUX:MATH:INV,C1,C1")

    def test_set_math_function_invalid(self):
        with self.assertRaises(ValueError):
            self.driver.set_math_function(1, 2, "DIV")

    def test_enable_math_on(self):
        self.driver.enable_math("ON")
        self.mock_resource.write.assert_any_call("MATH:STAT ON")

    def test_enable_math_off(self):
        self.driver.enable_math("OFF")
        self.mock_resource.write.assert_any_call("MATH:STAT OFF")

    def test_enable_math_invalid(self):
        with self.assertRaises(ValueError):
            self.driver.enable_math("MAYBE")


if __name__ == "__main__":
    unittest.main()
