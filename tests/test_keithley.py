import unittest
from unittest.mock import MagicMock
from instrumation.drivers.keithley import Keithley2000

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
            if "SYST:ERR?" in cmd: return '+0,"No error"'
            if ":READ?" in cmd: return "100.5"
            return ""
        self.mock_inst.query.side_effect = mock_query_res
        val = self.driver.measure_resistance()
        self.assertEqual(val.value, 100.5)
        self.assertEqual(val.unit, "Ohm")

    def test_measure_current(self):
        def mock_query_curr(cmd):
            if "SYST:ERR?" in cmd: return '+0,"No error"'
            if ":READ?" in cmd: return "0.01"
            return ""
        self.mock_inst.query.side_effect = mock_query_curr
        val = self.driver.measure_current()
        self.assertEqual(val.value, 0.01)
        self.assertEqual(val.unit, "A")

if __name__ == "__main__":
    unittest.main()
