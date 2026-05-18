import unittest
import os
import math
from instrumation.factory import get_instrument
from instrumation.exceptions import OverloadError, ConfigurationError
from instrumation.drivers.simulated import SimulatedElectronicLoad

class TestElectronicLoad(unittest.TestCase):
    def setUp(self):
        # Ensure we are in SIM mode
        os.environ["INSTRUMATION_MODE"] = "SIM"
        self.load = get_instrument("USB::SIM::LOAD", "LOAD")
        self.load.connect()

    def tearDown(self):
        self.load.disconnect()

    def test_identity(self):
        """Verify the mock electronic load identity fields."""
        self.assertEqual(self.load.get_id(), "SIM_ELOAD_3000")
        self.assertEqual(self.load.identity["manufacturer"], "SIM")
        self.assertEqual(self.load.identity["model"], "SIM_ELOAD_3000")

    def test_default_state(self):
        """Verify default values and settings upon connection."""
        self.assertEqual(self.load.get_mode(), "CC")
        self.assertFalse(self.load.get_input())
        self.assertEqual(self.load.get_current(), 0.0)
        self.assertEqual(self.load.get_voltage(), 0.0)
        self.assertEqual(self.load.get_resistance(), 10.0)
        self.assertEqual(self.load.get_power(), 0.0)

    def test_mode_transitions(self):
        """Verify transitions between CC, CV, CR, and CP modes."""
        for mode in ["CC", "CV", "CR", "CP"]:
            self.load.set_mode(mode)
            self.assertEqual(self.load.get_mode(), mode)

        with self.assertRaises(ValueError):
            self.load.set_mode("INVALID")

    def test_setting_guards(self):
        """Verify setting values check instrument limits."""
        # Current guards
        self.load.set_current(15.0)
        self.assertEqual(self.load.get_current(), 15.0)
        with self.assertRaises(ValueError):
            self.load.set_current(35.0) # exceeds max_current of 30.0A
        with self.assertRaises(ValueError):
            self.load.set_current(-1.0)

        # Voltage guards
        self.load.set_voltage(100.0)
        self.assertEqual(self.load.get_voltage(), 100.0)
        with self.assertRaises(ValueError):
            self.load.set_voltage(160.0) # exceeds max_voltage of 150.0V
        with self.assertRaises(ValueError):
            self.load.set_voltage(-5.0)

        # Resistance guards
        self.load.set_resistance(500.0)
        self.assertEqual(self.load.get_resistance(), 500.0)
        with self.assertRaises(ValueError):
            self.load.set_resistance(-10.0)
        with self.assertRaises(ValueError):
            self.load.set_resistance(0)

        # Power guards
        self.load.set_power(120.0)
        self.assertEqual(self.load.get_power(), 120.0)
        with self.assertRaises(ValueError):
            self.load.set_power(250.0) # exceeds max_power of 200.0W
        with self.assertRaises(ValueError):
            self.load.set_power(-10.0)

    def test_constant_current_physics(self):
        """Test the digital twin DC solver in Constant Current (CC) Mode."""
        self.load.set_mode("CC")
        self.load.set_current(2.0)
        self.load.set_input(True)

        # Theoretical values:
        # Vs = 12.0 V, Rs = 0.05 Ohm
        # I_act = 2.0 A
        # V_act = 12.0 - 2.0 * 0.05 = 11.9 V
        # P_act = 11.9 * 2.0 = 23.8 W
        measured_voltage = self.load.measure_voltage().value
        measured_current = self.load.measure_current().value
        measured_power = self.load.measure_power().value

        # Noise is +/- 0.1%, so check with comfortable delta
        self.assertAlmostEqual(measured_current, 2.0, delta=0.05)
        self.assertAlmostEqual(measured_voltage, 11.9, delta=0.05)
        self.assertAlmostEqual(measured_power, 23.8, delta=0.1)

        # Turn input off
        self.load.set_input(False)
        self.assertEqual(self.load.measure_current().value, 0.0)
        self.assertAlmostEqual(self.load.measure_voltage().value, 12.0, delta=0.01)
        self.assertEqual(self.load.measure_power().value, 0.0)

    def test_constant_voltage_physics(self):
        """Test the digital twin DC solver in Constant Voltage (CV) Mode."""
        self.load.set_mode("CV")
        self.load.set_voltage(11.5)
        self.load.set_input(True)

        # Theoretical values:
        # Regulated V_act = 11.5 V
        # Needed loop current I_act = (12.0 - 11.5) / 0.05 = 10.0 A
        # P_act = 11.5 * 10.0 = 115.0 W
        measured_voltage = self.load.measure_voltage().value
        measured_current = self.load.measure_current().value
        measured_power = self.load.measure_power().value

        self.assertAlmostEqual(measured_voltage, 11.5, delta=0.05)
        self.assertAlmostEqual(measured_current, 10.0, delta=0.05)
        self.assertAlmostEqual(measured_power, 115.0, delta=0.5)

    def test_constant_resistance_physics(self):
        """Test the digital twin DC solver in Constant Resistance (CR) Mode."""
        self.load.set_mode("CR")
        self.load.set_resistance(1.95)
        self.load.set_input(True)

        # Theoretical values:
        # Loop resistance = Rs + R_load = 0.05 + 1.95 = 2.0 Ohm
        # Loop current I_act = 12.0 / 2.0 = 6.0 A
        # Terminal V_act = 6.0 * 1.95 = 11.7 V
        # P_act = 11.7 * 6.0 = 70.2 W
        measured_voltage = self.load.measure_voltage().value
        measured_current = self.load.measure_current().value
        measured_power = self.load.measure_power().value

        self.assertAlmostEqual(measured_current, 6.0, delta=0.05)
        self.assertAlmostEqual(measured_voltage, 11.7, delta=0.05)
        self.assertAlmostEqual(measured_power, 70.2, delta=0.3)

    def test_constant_power_physics(self):
        """Test the digital twin DC solver in Constant Power (CP) Mode."""
        self.load.set_mode("CP")
        self.load.set_power(23.8)
        self.load.set_input(True)

        # Theoretical values:
        # Draws power P_act = 23.8 W
        # Since I_act = 2.0 A gives V_act = 11.9 V, P_act = 23.8 W
        measured_voltage = self.load.measure_voltage().value
        measured_current = self.load.measure_current().value
        measured_power = self.load.measure_power().value

        self.assertAlmostEqual(measured_power, 23.8, delta=0.1)
        self.assertAlmostEqual(measured_current, 2.0, delta=0.05)
        self.assertAlmostEqual(measured_voltage, 11.9, delta=0.05)

    def test_over_current_protection(self):
        """Verify Over-Current Protection (OCP) tripping behavior."""
        self.load.set_mode("CC")
        self.load.set_current(6.0)
        self.load.set_ocp(5.0) # limit below target current

        # Enabling input should trigger OCP instantly
        self.load.set_input(True)

        # Verify protection tripped
        self.assertFalse(self.load.get_input())
        self.assertEqual(self.load.measure_current().value, 0.0)
        self.assertEqual(self.load._protection_tripped, "OCP")

        # Enabling again should raise RuntimeError until cleared
        with self.assertRaises(RuntimeError):
            self.load.set_input(True)

        self.load.clear_protection()
        self.assertEqual(self.load._protection_tripped, False)

    def test_over_voltage_protection(self):
        """Verify Over-Voltage Protection (OVP) tripping behavior."""
        self.load.set_mode("CC")
        self.load.set_current(1.0)
        self.load.set_ovp(10.0) # source is 12V, so terminal voltage immediately trips OVP

        self.load.set_input(True)

        self.assertFalse(self.load.get_input())
        self.assertEqual(self.load._protection_tripped, "OVP")

    def test_over_power_protection(self):
        """Verify Over-Power Protection (OPP) tripping behavior."""
        self.load.set_mode("CC")
        self.load.set_current(5.0) # Power = (12 - 5 * 0.05) * 5 = 58.75 W
        self.load.set_opp(50.0) # Limit below 58.75W

        self.load.set_input(True)

        self.assertFalse(self.load.get_input())
        self.assertEqual(self.load._protection_tripped, "OPP")

if __name__ == "__main__":
    unittest.main()
