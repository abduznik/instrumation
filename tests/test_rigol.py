import unittest
from unittest.mock import MagicMock
from instrumation.drivers.rigol import RigolDSA

class TestRigolDSA(unittest.TestCase):
    def setUp(self):
        # Create a mock resource for the instrument
        self.mock_resource = MagicMock()
        self.mock_resource.query.return_value = "0.0"
        
        # Instantiate the driver with the mock resource
        # Note: We need to patch the instantiation mechanism if RigolDSA 
        # inherits from something that tries to open a connection in __init__.
        # Based on the code snippet, it likely inherits from SpectrumAnalyzer -> InstrumentDriver.
        # Assuming InstrumentDriver.__init__ takes a resource and stores it.
        # However, looking at RigolDSA source, it doesn't have an __init__ 
        # so it uses the parent's. 
        # We need to verify what 'self.inst' refers to in RigolDSA.
        
        # In base.py:
        # class InstrumentDriver(ABC):
        #     def __init__(self, resource):
        #         self.resource = resource
        #
        # But RigolDSA uses 'self.inst'.
        # We need to check if there's an intermediate class or if I should assume
        # self.inst is set up somewhere. 
        # Looking at previous files, real drivers often wrap a resource.
        # If RigolDSA expects 'self.inst' to be the resource, we should check parent classes.
        
        pass

    def test_peak_search(self):
        # Create a mock object that mimics the behavior of the instrument wrapper
        mock_inst = MagicMock()
        
        # We need to manually set the 'inst' attribute if the __init__ doesn't do it 
        # in the way we expect for the test, or we subclass/patch.
        # Let's create a subclass for testing that allows injecting the mock inst
        
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
        self.assertEqual(amp, -15.5)

    def test_get_marker_amplitude_invalid(self):
        mock_inst = MagicMock()
        mock_inst.query.return_value = "invalid"
        
        class TestableRigolDSA(RigolDSA):
            def __init__(self, inst):
                self.inst = inst

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
