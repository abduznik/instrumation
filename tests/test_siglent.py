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
        self.mock_resource.query.return_value = "C1:PAVA FREQ,1.23e+03Hz"
        freq = self.driver.measure_frequency()
        self.assertEqual(freq, 1230.0)

    def test_factory_registration(self):
        # Testing get_instrument for real hardware path
        with patch('instrumation.drivers.siglent.SiglentSDS.__init__', return_value=None):
            driver = get_instrument("USB::0x1AB1::0x04CE::INSTR", "SCOPE")
            self.assertIsInstance(driver, SiglentSDS)

    def test_auto_detection(self):
        # Testing connect_instrument auto-detection
        mock_rm = MagicMock()
        mock_res = MagicMock()
        mock_res.query.return_value = "SIGLENT,SDS1202X-E,SDS1EBX2R4567,1.3.9R1"
        
        with patch('pyvisa.ResourceManager', return_value=mock_rm):
            mock_rm.open_resource.return_value = mock_res
            driver = connect_instrument("USB::SIGLENT::SDS::INSTR")
            self.assertIsInstance(driver, SiglentSDS)
            mock_res.query.assert_called_with("*IDN?")

if __name__ == "__main__":
    unittest.main()
