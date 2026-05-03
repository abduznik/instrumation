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
            self.driver.inst.query.return_value = "1"
            self.driver.connected = True
        
        # Ensure we are NOT in SIM mode for these tests by default
        import os
        self._old_mode = os.environ.get("INSTRUMATION_MODE")
        os.environ["INSTRUMATION_MODE"] = "REAL"

    def tearDown(self):
        import os
        if self._old_mode is None:
            del os.environ["INSTRUMATION_MODE"]
        else:
            os.environ["INSTRUMATION_MODE"] = self._old_mode

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
        # Mocking binary data return with Siglent header
        header = b"C1:WF DAT2,"
        data = bytes([0, 1, 2, 3])
        footer = b"\n\r"
        self.mock_resource.read_raw.return_value = header + data + footer
        
        res = self.driver.get_waveform(1)
        self.assertEqual(res.value, [0.0, 1.0, 2.0, 3.0])
        self.assertEqual(res.unit, "V")

    def test_factory_registration(self):
        # Testing get_instrument for real hardware path
        # Mock RealDriver at the factory level AND the SiglentSDS connect method
        with patch('instrumation.factory.RealDriver') as mock_real, \
             patch('instrumation.drivers.siglent.SiglentSDS.connect'):
            mock_inst = mock_real.return_value
            mock_inst.get_id.return_value = "SIGLENT,SDS1000,1,1"
            
            driver = get_instrument("USB::0x1AB1::0x04CE::INSTR", "SCOPE")
            self.assertIsInstance(driver, SiglentSDS)

    def test_auto_detection(self):
        # Testing connect_instrument auto-detection
        mock_rm = MagicMock()
        mock_res = MagicMock()
        # Ensure IDN identifies it as Siglent so factory routes correctly
        mock_res.query.return_value = "SIGLENT,SDS1202X-E,SDS1EBX2R4567,1.3.9R1"
        
        with patch('instrumation.factory.get_rm', return_value=mock_rm), \
             patch('instrumation.factory.RealDriver') as mock_real:
            mock_real.return_value.get_id.return_value = "SIGLENT,SDS1202X-E,..."
            mock_rm.open_resource.return_value = mock_res
            driver = connect_instrument("USB::SIGLENT::SDS::INSTR")
            self.assertIsInstance(driver, SiglentSDS)

if __name__ == "__main__":
    unittest.main()
