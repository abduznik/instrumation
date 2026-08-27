import unittest

from instrumation.factory import _asrl_port_number, _skip_serial_probe


class TestSerialProbeFilter(unittest.TestCase):
    """Issue #151: probe_resource's ASRL filter used naive substring matching.

    `"ASRL" in res and any(p in res for p in ["1","2","3","4"])` wrongly
    matched ASRL10, ASRL21, etc. The fix extracts the numeric port suffix.
    """

    def test_asrl_port_number_low(self):
        self.assertEqual(_asrl_port_number("ASRL1::INSTR"), 1)
        self.assertEqual(_asrl_port_number("ASRL4::INSTR"), 4)

    def test_asrl_port_number_high(self):
        self.assertEqual(_asrl_port_number("ASRL10::INSTR"), 10)
        self.assertEqual(_asrl_port_number("ASRL21::INSTR"), 21)

    def test_asrl_port_number_non_asrl(self):
        self.assertIsNone(_asrl_port_number("TCPIP0::192.168.1.5::INSTR"))
        self.assertIsNone(_asrl_port_number("GPIB0::1::INSTR"))
        self.assertIsNone(_asrl_port_number("USB0::0x1234::INSTR"))

    def test_skip_serial_probe_only_low_ports(self):
        """Ports 1-4 skipped; 10+ must NOT be skipped (regression)."""
        self.assertTrue(_skip_serial_probe("ASRL1::INSTR"))
        self.assertTrue(_skip_serial_probe("ASRL2::INSTR"))
        self.assertTrue(_skip_serial_probe("ASRL3::INSTR"))
        self.assertTrue(_skip_serial_probe("ASRL4::INSTR"))

    def test_skip_serial_probe_does_not_skip_high_ports(self):
        """ASRL10/12/21 contain digits 1-4 as substrings -- must probe."""
        self.assertFalse(_skip_serial_probe("ASRL10::INSTR"))
        self.assertFalse(_skip_serial_probe("ASRL12::INSTR"))
        self.assertFalse(_skip_serial_probe("ASRL21::INSTR"))
        self.assertFalse(_skip_serial_probe("ASRL40::INSTR"))

    def test_skip_serial_probe_ignores_non_asrl_digits(self):
        """Non-ASRL resources containing digits 1-4 must not be skipped."""
        self.assertFalse(_skip_serial_probe("TCPIP0::192.168.1.4::INSTR"))
        self.assertFalse(_skip_serial_probe("GPIB0::14::INSTR"))
        self.assertFalse(_skip_serial_probe("USB0::0x1234::ABCD::INSTR"))

    def test_skip_serial_probe_lowercase_asrl(self):
        """Resource strings may arrive lowercased; case-insensitive match."""
        self.assertTrue(_skip_serial_probe("asrl1::instr"))
        self.assertFalse(_skip_serial_probe("asrl10::instr"))


if __name__ == "__main__":
    unittest.main()