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
                # This double doesn't model the SCPI error queue
                self.check_errors_enabled = False

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

    # ── Sweep / Step Tests (GH #202) ─────────────────────────────

    def test_configure_sweep_linear(self):
        self.driver.configure_sweep_linear(0.0, 5.0, 10, source="VOLT", delay=0.05)
        self.mock_inst.write.assert_any_call(":SOUR:FUNC VOLT")
        self.mock_inst.write.assert_any_call(":SOUR:SWEEP:TYPE LIN")
        self.mock_inst.write.assert_any_call(":SOUR:VOLT:START 0.0")
        self.mock_inst.write.assert_any_call(":SOUR:VOLT:STOP 5.0")
        self.mock_inst.write.assert_any_call(":SOUR:VOLT:STEP 10")
        self.mock_inst.write.assert_any_call(":SOUR:DEL 0.05")

    def test_configure_sweep_linear_invalid_source(self):
        with self.assertRaises(ValueError):
            self.driver.configure_sweep_linear(0, 5, 10, source="TEMP")

    def test_configure_sweep_linear_invalid_steps(self):
        with self.assertRaises(ValueError):
            self.driver.configure_sweep_linear(0, 5, 1)
        with self.assertRaises(ValueError):
            self.driver.configure_sweep_linear(0, 5, 2000)

    def test_configure_sweep_log(self):
        self.driver.configure_sweep_log(1.0, 1000.0, 50)
        self.mock_inst.write.assert_any_call(":SOUR:SWEEP:TYPE LOG")
        self.mock_inst.write.assert_any_call(":SOUR:VOLT:START 1.0")
        self.mock_inst.write.assert_any_call(":SOUR:VOLT:STOP 1000.0")
        self.mock_inst.write.assert_any_call(":SOUR:VOLT:STEP 50")

    def test_configure_sweep_log_negative_raises(self):
        with self.assertRaises(ValueError):
            self.driver.configure_sweep_log(-1.0, 10.0, 10)

    def test_configure_sweep_list(self):
        values = [0.0, 1.0, 2.5, 5.0]
        self.driver.configure_sweep_list(values)
        self.mock_inst.write.assert_any_call(":SOUR:SWEEP:TYPE LIST")
        self.mock_inst.write.assert_any_call(":SOUR:VOLT:LIST 0.0,1.0,2.5,5.0")

    def test_configure_sweep_list_too_few(self):
        with self.assertRaises(ValueError):
            self.driver.configure_sweep_list([1.0])

    def test_execute_sweep(self):
        # Mock the sweep result data — *OPC? must return "1" for wait_ready
        def mock_query(cmd):
            if "*OPC?" in cmd:
                return "1"
            if "FETC?" in cmd:
                return "1.01,2.02,3.03,4.04,5.05"
            return '+0,"No error"'
        self.mock_inst.query.side_effect = mock_query
        results = self.driver.execute_sweep()
        self.assertEqual(len(results), 5)
        self.assertAlmostEqual(results[0].value, 1.01)
        self.assertAlmostEqual(results[4].value, 5.05)
        for r in results:
            self.assertEqual(r.unit, "V")
        # Output should be turned ON then OFF
        self.mock_inst.write.assert_any_call(":OUTP ON")
        writes = [c for c in self.mock_inst.write.call_args_list if ":OUTP" in str(c)]
        self.assertTrue(any("OFF" in str(c) for c in writes))

    def test_step_sweep_convenience(self):
        """step_sweep should configure and execute in one call."""
        def mock_query(cmd):
            if "*OPC?" in cmd:
                return "1"
            if "FETC?" in cmd:
                return "0.5,1.0,1.5"
            return '+0,"No error"'
        self.mock_inst.query.side_effect = mock_query
        results = self.driver.step_sweep(0.0, 1.5, 3)
        self.assertEqual(len(results), 3)
        self.assertAlmostEqual(results[0].value, 0.5)
        self.assertAlmostEqual(results[2].value, 1.5)

    def test_configure_sweep_current_source(self):
        self.driver.configure_sweep_linear(0.0, 0.1, 5, source="CURR")
        self.mock_inst.write.assert_any_call(":SOUR:FUNC CURR")
        self.mock_inst.write.assert_any_call(":SOUR:CURR:START 0.0")
        self.mock_inst.write.assert_any_call(":SOUR:CURR:STOP 0.1")
        self.mock_inst.write.assert_any_call(":SOUR:CURR:STEP 5")


if __name__ == "__main__":
    unittest.main()
