import unittest
import os
from instrumation.factory import get_instrument, get_instrument_from_config

class TestFactory(unittest.TestCase):
    def setUp(self):
        # Ensure we are in SIM mode for these tests
        os.environ["INSTRUMATION_MODE"] = "SIM"

    def test_get_instrument_valid(self):
        driver = get_instrument("USB::0x1234::SIM", "DMM")
        self.assertIsNotNone(driver)

    def test_get_instrument_invalid_type(self):
        with self.assertRaises(ValueError) as cm:
            get_instrument("USB::0x1234::SIM", "INVALID")
        self.assertIn("Unknown driver type", str(cm.exception))

    def test_get_instrument_from_config_valid(self):
        config = {"address": "USB::0x1234::SIM", "type": "DMM"}
        driver = get_instrument_from_config(config)
        self.assertIsNotNone(driver)

    def test_get_instrument_from_config_missing_address(self):
        config = {"type": "DMM"}
        with self.assertRaises(ValueError) as cm:
            get_instrument_from_config(config)
        self.assertEqual(str(cm.exception), "Missing required configuration key: 'address'")

    def test_get_instrument_from_config_missing_type(self):
        config = {"address": "USB::0x1234::SIM"}
        with self.assertRaises(ValueError) as cm:
            get_instrument_from_config(config)
        self.assertEqual(str(cm.exception), "Missing required configuration key: 'type'")

if __name__ == "__main__":
    unittest.main()
