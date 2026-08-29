import unittest
import os
from instrumation.factory import get_instrument, get_instrument_from_config, _discovery_priority

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
        self.assertIn("No simulated driver found", str(cm.exception))

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


class TestDiscoveryPriority(unittest.TestCase):
    """Covers GH #159: AUTO discovery sort key is a naive boolean, not a tier ranking."""

    def test_tcpip_ranks_above_usb(self):
        self.assertGreater(
            _discovery_priority("TCPIP0::192.168.1.5::INSTR"),
            _discovery_priority("USB0::0x2A8D::0x0101::SN::0::INSTR"),
        )

    def test_usb_ranks_above_gpib(self):
        self.assertGreater(
            _discovery_priority("USB0::0x2A8D::0x0101::SN::0::INSTR"),
            _discovery_priority("GPIB0::5::INSTR"),
        )

    def test_gpib_ranks_above_serial(self):
        self.assertGreater(
            _discovery_priority("GPIB0::5::INSTR"),
            _discovery_priority("ASRL5::INSTR"),
        )

    def test_hislip_same_tier_as_tcpip(self):
        self.assertEqual(
            _discovery_priority("TCPIP0::192.168.1.5::hislip0::INSTR"),
            _discovery_priority("TCPIP0::192.168.1.5::INSTR"),
        )

    def test_candidates_sort_by_tier_stably(self):
        resources = [
            "ASRL5::INSTR",
            "GPIB0::1::INSTR",
            "USB0::0x1234::INSTR",
            "TCPIP0::1.2.3.4::INSTR",
        ]
        ordered = sorted(resources, key=_discovery_priority, reverse=True)
        self.assertEqual(ordered[0], "TCPIP0::1.2.3.4::INSTR")
        self.assertEqual(ordered[1], "USB0::0x1234::INSTR")
        self.assertEqual(ordered[2], "GPIB0::1::INSTR")
        self.assertEqual(ordered[3], "ASRL5::INSTR")

    def test_same_tier_preserves_input_order(self):
        resources = ["TCPIP0::10.0.0.2::INSTR", "TCPIP0::10.0.0.1::INSTR"]
        ordered = sorted(resources, key=_discovery_priority, reverse=True)
        self.assertEqual(ordered, resources)

if __name__ == "__main__":
    unittest.main()
