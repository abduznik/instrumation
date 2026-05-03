import unittest
from unittest.mock import MagicMock
from instrumation.drivers.tektronix import TektronixTDS

class TestTektronixTDS(unittest.TestCase):
    def setUp(self):
        self.mock_inst = MagicMock()
        # Handle multiple calls to query
        def mock_query(cmd):
            if "SYST:ERR?" in cmd:
                return '+0,"No error"'
            if "*IDN?" in cmd:
                return "TEKTRONIX,TDS123,123,1.0"
            if "WFMPRE:YMULT?" in cmd:
                return "0.01"
            if "WFMPRE:YOFF?" in cmd:
                return "0"
            if "WFMPRE:YZERO?" in cmd:
                return "0"
            return ""

        self.mock_inst.query.side_effect = mock_query
        self.mock_inst.query_binary_values.return_value = [100, 200, 300, 400]
        
        class TestableTektronixTDS(TektronixTDS):
            def __init__(self, inst):
                super().__init__("USB::TEK")
                self.inst = inst
                self.connected = True
            
            def connect(self): pass
            def disconnect(self): pass
            def get_id(self): return "TEK_IDN"
                
        self.driver = TestableTektronixTDS(self.mock_inst)

    def test_run(self):
        self.driver.run()
        self.mock_inst.write.assert_called_with(":ACQUIRE:STATE ON")

    def test_stop(self):
        self.driver.stop()
        self.mock_inst.write.assert_called_with(":ACQUIRE:STATE OFF")

    def test_get_waveform(self):
        data = self.driver.get_waveform(1)
        self.assertEqual(data.value, [1.0, 2.0, 3.0, 4.0])
        self.assertEqual(data.unit, "V")

if __name__ == "__main__":
    unittest.main()
