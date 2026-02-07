import unittest
from unittest.mock import MagicMock
from instrumation.drivers.tektronix import TektronixTDS

class TestTektronixTDS(unittest.TestCase):
    def setUp(self):
        self.mock_resource = MagicMock()
        self.driver = TektronixTDS(self.mock_resource)

    def test_run(self):
        self.driver.run()
        self.mock_resource.write.assert_called_with(":ACQUIRE:STATE ON")

    def test_stop(self):
        self.driver.stop()
        self.mock_resource.write.assert_called_with(":ACQUIRE:STATE OFF")

    def test_get_waveform(self):
        # Setup mock response for :CURVE?
        self.mock_resource.query.return_value = "1.0,2.0,3.0,-1.0"
        
        data = self.driver.get_waveform(1)
        
        # Verify sequence of commands
        self.mock_resource.write.assert_any_call(":DATA:SOURCE CH1")
        self.mock_resource.write.assert_any_call(":DATA:ENC ASC")
        self.mock_resource.query.assert_called_with(":CURVE?")
        
        self.assertEqual(data, [1.0, 2.0, 3.0, -1.0])

if __name__ == "__main__":
    unittest.main()
