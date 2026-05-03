import unittest
from unittest.mock import MagicMock, patch
from instrumation.drivers.tdk import TDKLambdaZPlus

class TestTDKLambdaZPlus(unittest.TestCase):
    @patch('instrumation.drivers.real.pyvisa.ResourceManager')
    def setUp(self, mock_rm_cls):
        self.mock_inst = MagicMock()
        def mock_query(cmd):
            if "SYST:ERR?" in cmd: return '+0,"No error"'
            if ":VOLT?" in cmd: return "12.5"
            if ":MEAS:CURR?" in cmd: return "1.234"
            if "*IDN?" in cmd: return "TDK,Z+,1,1"
            return "0"
        self.mock_inst.query.side_effect = mock_query
        
        mock_rm = mock_rm_cls.return_value
        mock_rm.open_resource.return_value = self.mock_inst
        
        self.driver = TDKLambdaZPlus("GPIB0::1::INSTR")
        self.driver.connect()

    def test_set_voltage(self):
        self.driver.set_voltage(5.0)
        self.mock_inst.write.assert_called_with(":VOLT 5.0")

    def test_get_voltage(self):
        val = self.driver.get_voltage()
        self.assertEqual(val, 12.5)

    def test_get_current(self):
        val = self.driver.get_current()
        self.assertEqual(val.value, 1.234)
        self.assertEqual(val.unit, "A")

    def test_set_output(self):
        self.driver.set_output(True)
        self.mock_inst.write.assert_called_with(":OUTP ON")

    def test_ovp(self):
        self.driver.set_ovp(40.0)
        self.mock_inst.write.assert_called_with(":VOLT:PROT 40.0")

    def test_measure_actual(self):
        # Override the setup side_effect for this test
        self.mock_inst.query.side_effect = None
        self.mock_inst.query.return_value = "12.495"
        res = self.driver.measure_voltage_actual()
        self.assertEqual(res.value, 12.495)
        self.assertEqual(res.unit, "V")

    def test_clear_protection(self):
        self.driver.clear_protection()
        self.mock_inst.write.assert_called_with(":OUTP:PROT:CLE")

if __name__ == "__main__":
    unittest.main()
