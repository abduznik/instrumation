import unittest
from unittest.mock import MagicMock
from instrumation.drivers.keithley import Keithley2000, Keithley2400
from instrumation.results import MeasurementResult


class TestKeithley2000(unittest.TestCase):
    def setUp(self):
        self.mock_inst = MagicMock()
        def mock_query(cmd):
            if "SYST:ERR?" in cmd:
                return '+0,"No error"'
            if ":READ?" in cmd:
                return "5.5"
            if ":MEAS:FREQ?" in cmd:
                return "1000.0"
            return ""
        self.mock_inst.query.side_effect = mock_query

        class TestableKeithley2000(Keithley2000):
            def __init__(self, inst):
                super().__init__("USB::KEITHLEY")
                self.inst = inst
                self.connected = True
            
            def connect(self): pass
            def disconnect(self): pass
            def get_id(self): return "KEITHLEY_2000"
            
        self.driver = TestableKeithley2000(self.mock_inst)

    def test_measure_voltage(self):
        val = self.driver.measure_voltage()
        self.assertEqual(val.value, 5.5)
        self.assertEqual(val.unit, "V")

    def test_measure_resistance(self):
        def mock_query_res(cmd):
            if "SYST:ERR?" in cmd:
                return '+0,"No error"'
            if ":READ?" in cmd:
                return "100.5"
            return ""

        self.mock_inst.query.side_effect = mock_query_res
        val = self.driver.measure_resistance()
        self.assertEqual(val.value, 100.5)
        self.assertEqual(val.unit, "Ohm")

    def test_measure_current(self):
        def mock_query_curr(cmd):
            if "SYST:ERR?" in cmd:
                return '+0,"No error"'
            if ":READ?" in cmd:
                return "0.01"
            return ""
        self.mock_inst.query.side_effect = mock_query_curr
        val = self.driver.measure_current()
        self.assertEqual(val.value, 0.01)
        self.assertEqual(val.unit, "A")


class TestKeithley2400(unittest.TestCase):
    def setUp(self):
        self.mock_inst = MagicMock()
        self.mock_inst.query.return_value = '+0,"No error"'
        self.mock_inst.read.return_value = ""

        class TestableKeithley2400(Keithley2400):
            def __init__(self, inst):
                super().__init__("USB::KEITHLEY2400")
                self.inst = inst
                self.connected = True

            def connect(self): pass
            def disconnect(self): pass
            def get_id(self): return "KEITHLEY_2400"

        self.driver = TestableKeithley2400(self.mock_inst)

    # ── Source functions (PowerSupply) ─────────────────────

    def test_set_get_voltage(self):
        self.mock_inst.query.return_value = "5.0"
        self.driver.set_voltage(5.0)
        self.mock_inst.write.assert_any_call(":SOUR:VOLT 5.0")
        val = self.driver.get_voltage()
        self.assertEqual(val, 5.0)
        self.mock_inst.query.assert_any_call(":SOUR:VOLT?")

    def test_set_current_limit(self):
        self.driver.set_current_limit(0.1)
        self.mock_inst.write.assert_any_call(":SOUR:CURR 0.1")

    def test_set_output_on(self):
        self.mock_inst.query.return_value = "1"
        self.driver.set_output(True)
        self.mock_inst.write.assert_any_call(":OUTP ON")
        self.assertTrue(self.driver.get_output())

    def test_set_output_off(self):
        self.mock_inst.query.return_value = "0"
        self.driver.set_output(False)
        self.assertTrue(not self.driver.get_output())

    def test_set_ovp(self):
        self.driver.set_ovp(21.0)
        self.mock_inst.write.assert_any_call(":SOUR:VOLT:PROT 21.0")

    def test_set_ocp(self):
        self.driver.set_ocp(0.105)
        self.mock_inst.write.assert_any_call(":SOUR:CURR:PROT 0.105")

    def test_measure_power(self):
        self.mock_inst.query.side_effect = ["5.0", "0.05", ""]
        res = self.driver.measure_power()
        self.assertAlmostEqual(res.value, 0.25)
        self.assertEqual(res.unit, "W")

    def test_get_mode(self):
        self.mock_inst.query.return_value = "VOLT"
        mode = self.driver.get_mode()
        self.assertEqual(mode, "CV")

    # ── Measure functions (Multimeter) ─────────────────────

    def test_measure_voltage(self):
        self.mock_inst.query.return_value = "5.0,0.0,1000.0,0.1"
        res = self.driver.measure_voltage()
        self.assertEqual(res.value, 5.0)
        self.assertEqual(res.unit, "V")

    def test_measure_current(self):
        self.mock_inst.query.return_value = "0.0,0.05,0.0,0.1"
        res = self.driver.measure_current()
        self.assertEqual(res.value, 0.05)
        self.assertEqual(res.unit, "A")

    def test_measure_resistance(self):
        self.mock_inst.query.return_value = "0,0,500.0,0"
        res = self.driver.measure_resistance()
        self.assertEqual(res.value, 500.0)
        self.assertEqual(res.unit, "Ohm")

    def test_shutdown_safety(self):
        self.driver.shutdown_safety()
        self.mock_inst.write.assert_any_call(":OUTP OFF")
        self.mock_inst.write.assert_any_call(":SOUR:VOLT 0")
        self.mock_inst.write.assert_any_call(":SOUR:CURR 0")


if __name__ == "__main__":
    unittest.main()
