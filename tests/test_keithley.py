import unittest
from unittest.mock import MagicMock
from instrumation.drivers.keithley import Keithley2000

class TestKeithley2000(unittest.TestCase):
    def setUp(self):
        self.mock_resource = MagicMock()
        self.driver = Keithley2000(self.mock_resource)

    def test_measure_voltage(self):
        self.mock_resource.query.return_value = "3.3"
        val = self.driver.measure_voltage()
        self.mock_resource.query.assert_called_with(":MEAS:VOLT:DC?")
        self.assertEqual(val, 3.3)

    def test_measure_resistance(self):
        self.mock_resource.query.return_value = "1000.5"
        val = self.driver.measure_resistance()
        self.mock_resource.query.assert_called_with(":MEAS:RES?")
        self.assertEqual(val, 1000.5)

    def test_measure_current(self):
        self.mock_resource.query.return_value = "0.05"
        val = self.driver.measure_current()
        self.mock_resource.query.assert_called_with(":MEAS:CURR:DC?")
        self.assertEqual(val, 0.05)

if __name__ == "__main__":
    unittest.main()
