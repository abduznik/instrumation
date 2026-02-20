import unittest
from unittest.mock import MagicMock, patch
from instrumation.drivers.siglent import SiglentSDS

class TestSiglentSDS(unittest.TestCase):
    def setUp(self):
        self.mock_resource = MagicMock()
        # Mock pyvisa.ResourceManager
        with patch('pyvisa.ResourceManager'):
            self.driver = SiglentSDS("USB0::0x1AB1::0x04CE::SDS1000::INSTR")
            self.driver.inst = self.mock_resource
            self.driver.connected = True

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
        # Setup mock behavior for manual read/write if used, 
        # or simplified query_binary_values
        
        # In the implementation, I used query_binary_values after reading the prefix
        self.mock_resource.read_bytes.return_value = b"C1:WF DAT2,"
        self.mock_resource.query_binary_values.return_value = [0, 1, 2, 3]
        
        data = self.driver.get_waveform(1)
        
        self.mock_resource.write.assert_called_with("C1:WF? DAT2")
        self.mock_resource.read_bytes.assert_called_once()
        self.assertEqual(data, [0.0, 1.0, 2.0, 3.0])

    def test_measure_frequency(self):
        self.mock_resource.query.return_value = "C1:PAVA FREQ,1.23e+03V"
        freq = self.driver.measure_frequency()
        self.assertEqual(freq, 1230.0)

if __name__ == "__main__":
    unittest.main()
