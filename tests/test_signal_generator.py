import unittest
from unittest.mock import MagicMock
from instrumation.drivers.base import SignalGenerator

class TestSignalGenerator(unittest.TestCase):
    def test_signal_generator_interface(self):
        """Verify that SignalGenerator requires abstract methods to be implemented."""
        # Create a mock implementation
        class MockSigGen(SignalGenerator):
            def connect(self): pass
            def disconnect(self): pass
            def get_id(self): return "MOCK"
            def measure_frequency(self): return 0.0
            def measure_duty_cycle(self): return 0.0
            def measure_v_peak_to_peak(self): return 0.0
            def set_frequency(self, hz): self.freq = hz
            def set_amplitude(self, dbm): self.amp = dbm
            def set_output(self, state): self.output = state

        mock_inst = MagicMock()
        driver = MockSigGen(mock_inst)
        
        driver.set_frequency(1e9)
        self.assertEqual(driver.freq, 1e9)
        
        driver.set_amplitude(-10.0)
        self.assertEqual(driver.amp, -10.0)
        
        driver.set_output(True)
        self.assertTrue(driver.output)

    def test_abstract_instantiation_fails(self):
        """Verify that SignalGenerator cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            SignalGenerator("some_resource")

if __name__ == "__main__":
    unittest.main()
