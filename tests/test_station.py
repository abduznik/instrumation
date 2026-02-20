import unittest
import logging
from unittest.mock import MagicMock, patch
from instrumation.station import Station

class TestStation(unittest.TestCase):
    def setUp(self):
        # Mocking toml.load to avoid missing file issues in setup
        with patch('os.path.exists', return_value=False):
            self.station = Station("dummy.toml")

    @patch('os.path.exists', return_value=True)
    @patch('toml.load')
    @patch('instrumation.station.get_instrument')
    def test_load_valid_config(self, mock_get_inst, mock_toml_load, mock_exists):
        # Setup mock data
        mock_toml_load.return_value = {
            "instruments": {
                "sa_main": {"driver": "SA", "address": "TCPIP::1.2.3.4::INSTR"},
                "psu_val": {"driver": "PSU", "address": "USB0::0x1234::INSTR"}
            }
        }
        mock_inst1 = MagicMock()
        mock_inst2 = MagicMock()
        mock_get_inst.side_effect = [mock_inst1, mock_inst2]

        # Reload station with mocked config
        self.station.load()

        # Verify attributes attached to instr namespace
        self.assertTrue(hasattr(self.station.instr, "sa_main"))
        self.assertTrue(hasattr(self.station.instr, "psu_val"))
        self.assertEqual(self.station.instr.sa_main, mock_inst1)
        self.assertEqual(self.station.instr.psu_val, mock_inst2)

    @patch('os.path.exists', return_value=True)
    @patch('toml.load')
    @patch('instrumation.station.get_instrument')
    def test_reserved_names_in_namespace(self, mock_get_inst, mock_toml_load, mock_exists):
        # Setup mock data with a name that was previously reserved like 'connect'
        mock_toml_load.return_value = {
            "instruments": {
                "connect": {"driver": "DMM", "address": "GPIB::1::INSTR"}
            }
        }
        mock_inst = MagicMock()
        mock_get_inst.return_value = mock_inst

        # Reload station
        self.station.load()

        # 'connect' should be fine inside 'instr' and NOT collide with Station.connect
        self.assertTrue(hasattr(self.station.instr, "connect"))
        self.assertEqual(self.station.instr.connect, mock_inst)
        self.assertNotEqual(self.station.connect, mock_inst) # Method remains intact

    @patch('os.path.exists', return_value=False)
    def test_missing_file_handled_gracefully(self, mock_exists):
        # Station initialized in setUp already calls load() with missing file
        # We just verify it didn't crash and has no instruments
        self.assertEqual(len(self.station.instruments), 0)

    @patch('os.path.exists', return_value=True)
    @patch('toml.load')
    def test_invalid_config_raises_validation_error(self, mock_toml_load, mock_exists):
        # Missing 'address' field
        mock_toml_load.return_value = {
            "instruments": {
                "bad_inst": {"driver": "SA"}
            }
        }
        with self.assertRaises(ValueError):
            self.station.load()

    @patch('os.path.exists', return_value=True)
    @patch('toml.load', side_effect=Exception("TOML Syntax Error"))
    def test_invalid_toml_raises_exception(self, mock_toml_load, mock_exists):
        with self.assertRaises(Exception):
            self.station.load()

    @patch('os.path.exists', return_value=True)
    @patch('toml.load')
    @patch('instrumation.station.get_instrument')
    def test_logging_on_connect(self, mock_get_inst, mock_toml_load, mock_exists):
        mock_toml_load.return_value = {
            "instruments": {"sa": {"driver": "SA", "address": "ADDR"}}
        }
        mock_inst = MagicMock()
        mock_inst.resource = "ADDR"
        mock_get_inst.return_value = mock_inst
        
        self.station.load()
        
        with self.assertLogs('instrumation.station', level='INFO') as cm:
            self.station.connect()
            self.assertTrue(any("Connected to sa at ADDR" in output for output in cm.output))

if __name__ == "__main__":
    unittest.main()
