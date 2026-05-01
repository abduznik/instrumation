import unittest
from unittest.mock import MagicMock
from instrumation.drivers.rigol import RigolDSA
from instrumation.results import MeasurementResult

class TestRigolDSA(unittest.TestCase):
    def test_peak_search(self):
        mock_inst = MagicMock()
        mock_inst.query.return_value = '+0,"No error"'
        
        class TestableRigolDSA(RigolDSA):
            def __init__(self, inst):
                super().__init__("USB::MOCK")
                self.inst = inst
                self.connected = True
            
            def connect(self): pass
            def disconnect(self): pass
            def get_id(self): return "MOCK"
                
        driver = TestableRigolDSA(mock_inst)
        driver.peak_search()
        mock_inst.write.assert_called_with(":CALC:MARK:MAX")

    def test_get_marker_amplitude(self):
        mock_inst = MagicMock()
        mock_inst.query.return_value = "-15.5"

        class TestableRigolDSA(RigolDSA):
            def __init__(self, inst):
                super().__init__("USB::MOCK")
                self.inst = inst
                self.connected = True
            
            def connect(self): pass
            def disconnect(self): pass
            def get_id(self): return "MOCK"
        
        driver = TestableRigolDSA(mock_inst)
        amp = driver.get_marker_amplitude()
        mock_inst.query.assert_called_with(":CALC:MARK:Y?")
        self.assertEqual(amp.value, -15.5)
        self.assertEqual(amp.unit, "dBm")

if __name__ == "__main__":
    unittest.main()
