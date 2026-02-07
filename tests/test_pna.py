import unittest
from unittest.mock import MagicMock, patch
from instrumation.drivers.keysight import KeysightPNA

class TestKeysightPNA(unittest.TestCase):
    @patch('instrumation.drivers.real.pyvisa.ResourceManager')
    def setUp(self, mock_rm_cls):
        self.mock_inst = MagicMock()
        mock_rm = mock_rm_cls.return_value
        mock_rm.open_resource.return_value = self.mock_inst
        
        self.driver = KeysightPNA("GPIB0::16::INSTR")
        self.driver.connect()

    def test_set_start_frequency(self):
        self.driver.set_start_frequency(1e9)
        self.mock_inst.write.assert_called_with("SENS:FREQ:STAR 1000000000.0")

    def test_set_stop_frequency(self):
        self.driver.set_stop_frequency(2e9)
        self.mock_inst.write.assert_called_with("SENS:FREQ:STOP 2000000000.0")

    def test_set_points(self):
        self.driver.set_points(201)
        self.mock_inst.write.assert_called_with("SENS:SWE:POIN 201")

    def test_get_trace_data(self):
        self.mock_inst.query.return_value = "-20.5, -30.2, -10.1"
        data = self.driver.get_trace_data("S21_Meas")
        
        self.mock_inst.write.assert_called_with("CALC:PAR:SEL 'S21_Meas'")
        self.mock_inst.query.assert_called_with("CALC:DATA? FDATA")
        self.assertEqual(data, [-20.5, -30.2, -10.1])

if __name__ == "__main__":
    unittest.main()
