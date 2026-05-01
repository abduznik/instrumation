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
        self.mock_inst.query_binary_values.return_value = [1.0, 2.0, 3.0]
        data = self.driver.get_trace_data("MyTrace")
        # Verify sequence: Select trace -> Set binary -> Query binary
        self.mock_inst.write.assert_any_call("CALC:PAR:SEL 'MyTrace'")
        self.mock_inst.write.assert_any_call("FORM:DATA REAL,32")
        self.mock_inst.query_binary_values.assert_called_with("CALC:DATA? FDATA", datatype='f', is_big_endian=False)
        self.assertEqual(data.value, [1.0, 2.0, 3.0])
        self.assertEqual(data.unit, "dB")

if __name__ == "__main__":
    unittest.main()
