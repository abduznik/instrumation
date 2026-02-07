import unittest
from unittest.mock import MagicMock, patch
from instrumation.drivers.tdk import TDKLambdaZPlus

class TestTDKLambdaZPlus(unittest.TestCase):
    @patch('instrumation.drivers.real.pyvisa.ResourceManager')
    def setUp(self, mock_rm_cls):
        # Create a mock resource
        self.mock_inst = MagicMock()
        self.mock_inst.query.return_value = "0.0"
        
        # Configure the ResourceManager mock to return our mock resource
        mock_rm = mock_rm_cls.return_value
        mock_rm.open_resource.return_value = self.mock_inst
        
        # Initialize the driver
        self.driver = TDKLambdaZPlus("GPIB0::1::INSTR")
        
        # Manually connect to populate self.inst
        self.driver.connect()

    def test_set_voltage(self):
        self.driver.set_voltage(5.0)
        self.mock_inst.write.assert_called_with(":VOLT 5.0")

    def test_get_voltage(self):
        self.mock_inst.query.return_value = "5.001"
        val = self.driver.get_voltage()
        self.mock_inst.query.assert_called_with(":MEAS:VOLT?")
        self.assertEqual(val, 5.001)

    def test_set_current_limit(self):
        self.driver.set_current_limit(1.5)
        self.mock_inst.write.assert_called_with(":CURR 1.5")

    def test_get_current(self):
        self.mock_inst.query.return_value = "0.1"
        val = self.driver.get_current()
        self.mock_inst.query.assert_called_with(":MEAS:CURR?")
        self.assertEqual(val, 0.1)

    def test_set_output(self):
        self.driver.set_output(True)
        self.mock_inst.write.assert_called_with(":OUTP ON")
        
        self.driver.set_output(False)
        self.mock_inst.write.assert_called_with(":OUTP OFF")

if __name__ == "__main__":
    unittest.main()
