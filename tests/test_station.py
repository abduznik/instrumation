import unittest
from unittest.mock import MagicMock, patch, mock_open
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

        # Verify attributes attached
        self.assertTrue(has_attr(self.station, "sa_main"))
        self.assertTrue(has_attr(self.station, "psu_val"))
        self.assertEqual(self.station.sa_main, mock_inst1)
        self.assertEqual(self.station.psu_val, mock_inst2)

    @patch('os.path.exists', return_value=True)
    @patch('toml.load')
    @patch('instrumation.station.get_instrument')
    def test_reserved_names(self, mock_get_inst, mock_toml_load, mock_exists):
        # Setup mock data with a reserved name 'connect'
        mock_toml_load.return_value = {
            "instruments": {
                "connect": {"driver": "DMM", "address": "GPIB::1::INSTR"}
            }
        }
        mock_inst = MagicMock()
        mock_get_inst.return_value = mock_inst

        # Reload station
        self.station.load()

        # 'connect' should be renamed to 'inst_connect'
        self.assertFalse(has_attr(self.station, "connect") and self.station.connect == mock_inst)
        self.assertTrue(has_attr(self.station, "inst_connect"))
        self.assertEqual(self.station.inst_connect, mock_inst)

    @patch('os.path.exists', return_value=False)
    def test_missing_file_handled_gracefully(self, mock_exists):
        # Station initialized in setUp already calls load() with missing file
        # We just verify it didn't crash and has no instruments
        self.assertEqual(len(self.station.instruments), 0)

    @patch('os.path.exists', return_value=True)
    @patch('toml.load', side_effect=Exception("TOML Syntax Error"))
    def test_invalid_toml_handled_gracefully(self, mock_toml_load, mock_exists):
        self.station.load()
        self.assertEqual(len(self.station.instruments), 0)

def has_attr(obj, name):
    # Helper to check if attribute exists and is NOT a method from the class itself
    return hasattr(obj, name) and name not in Station.__dict__

if __name__ == "__main__":
    unittest.main()
