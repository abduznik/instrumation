import unittest
from unittest.mock import MagicMock
from instrumation.drivers.rigol import RigolDSA

class TestRigolDSA(unittest.TestCase):
    def setUp(self):
        pass

    def test_peak_search(self):
        mock_inst = MagicMock()
        
        class TestableRigolDSA(RigolDSA):
            def __init__(self, inst):
                self.inst = inst
                self.connected = True
            
            def connect(self): pass
            def disconnect(self): pass
            def get_id(self): return "MOCK"
            def measure_frequency(self): return 0.0
            def measure_duty_cycle(self): return 0.0
            def measure_v_peak_to_peak(self): return 0.0
                
        driver = TestableRigolDSA(mock_inst)
        driver.peak_search()
        mock_inst.write.assert_called_with(":CALC:MARK:MAX")

    def test_get_marker_amplitude(self):
        mock_inst = MagicMock()
        mock_inst.query.return_value = "-15.5"

        class TestableRigolDSA(RigolDSA):
            def __init__(self, inst):
                self.inst = inst
                self.connected = True
            
            def connect(self): pass
            def disconnect(self): pass
            def get_id(self): return "MOCK"
            def measure_frequency(self): return 0.0
            def measure_duty_cycle(self): return 0.0
            def measure_v_peak_to_peak(self): return 0.0
        
        driver = TestableRigolDSA(mock_inst)
        amp = driver.get_marker_amplitude()
        mock_inst.query.assert_called_with(":CALC:MARK:Y?")
        self.assertEqual(amp.value, -15.5)
        self.assertEqual(amp.unit, "dBm")

    def test_get_marker_amplitude_invalid(self):
        mock_inst = MagicMock()
        mock_inst.query.return_value = "invalid"
        
        class TestableRigolDSA(RigolDSA):
            def __init__(self, inst):
                self.inst = inst
                self.connected = True

            def connect(self): pass
            def disconnect(self): pass
            def get_id(self): return "MOCK"
            def measure_frequency(self): return 0.0
            def measure_duty_cycle(self): return 0.0
            def measure_v_peak_to_peak(self): return 0.0
        
        driver = TestableRigolDSA(mock_inst)
        with self.assertRaises(ValueError):
            driver.get_marker_amplitude()

if __name__ == "__main__":
    unittest.main()
