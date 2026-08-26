import unittest
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
        mock_inst.connected = False  # freshly added instrument not yet connected
        mock_get_inst.return_value = mock_inst
        
        self.station.load()
        
        with self.assertLogs('instrumation.station', level='INFO') as cm:
            self.station.connect()
            self.assertTrue(any("Connected to sa at ADDR" in output for output in cm.output))

    @patch('os.path.exists', return_value=True)
    @patch('toml.load')
    @patch('instrumation.station.get_instrument')
    def test_connect_skips_already_connected_instrument(self, mock_get_inst, mock_toml_load, mock_exists):
        """Regression test for #156: connect() must not double-connect.

        get_instrument() already connects drivers before they are stored, so a
        driver whose ``connected`` flag is already True must not have connect()
        called again through the Station flow.
        """
        mock_toml_load.return_value = {
            "instruments": {
                "sa_already": {"driver": "SA", "address": "ADDR1"},
                "sa_fresh": {"driver": "SA", "address": "ADDR2"},
            }
        }
        already_connected = MagicMock()
        already_connected.resource = "ADDR1"
        already_connected.connected = True

        fresh = MagicMock()
        fresh.resource = "ADDR2"
        fresh.connected = False

        mock_get_inst.side_effect = [already_connected, fresh]

        self.station.load()

        self.station.connect()

        # The already-connected instrument must NOT be re-connected.
        already_connected.connect.assert_not_called()
        # Only the fresh instrument gets connected.
        fresh.connect.assert_called_once()

    @patch('os.path.exists', return_value=True)
    @patch('toml.load')
    @patch('instrumation.station.get_instrument')
    def test_connect_calls_connect_exactly_once_per_instrument(self, mock_get_inst, mock_toml_load, mock_exists):
        """Acceptance criterion for #156: connect() is called exactly once.

        Even when Station.connect() is invoked after load (where the driver is
        already connected), calling connect() again must not re-open the VISA
        resource. Repeated Station.connect() calls remain no-ops for connected
        instruments.
        """
        mock_toml_load.return_value = {
            "instruments": {"dmm": {"driver": "DMM", "address": "GPIB::1::INSTR"}}
        }
        # Simulate the real flow: get_instrument() connects the driver so its
        # connected flag is already True when the Station stores it.
        mock_inst = MagicMock()
        mock_inst.resource = "GPIB::1::INSTR"
        mock_inst.connected = True
        mock_get_inst.return_value = mock_inst

        self.station.load()

        # connect() once
        self.station.connect()
        # connect() again -- still should not re-connect
        self.station.connect()

        mock_inst.connect.assert_not_called()

if __name__ == "__main__":
    unittest.main()
