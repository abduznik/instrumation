from unittest.mock import patch, MagicMock
from instrumation.cli import main
import sys
import time

def test_cli_scan():
    """Test that the scan command calls the scanner."""
    with patch('instrumation.cli.scan') as mock_scan:
        mock_scan.return_value = [{"type": "test", "id": "123", "desc": "desc"}]
        with patch.object(sys, 'argv', ['instrumation', 'scan']):
            main()
        mock_scan.assert_called_once()

def test_cli_measure():
    """Test that the measure command calls get_instrument and the requested method."""
    mock_instr = MagicMock()
    mock_instr.__enter__.return_value = mock_instr
    mock_instr.measure_voltage.return_value = "Result"
    
    with patch('instrumation.cli.get_instrument') as mock_get:
        mock_get.return_value = mock_instr
        with patch.object(sys, 'argv', ['instrumation', 'measure', 'ADDR', 'DMM', 'measure_voltage']):
            main()
        
        mock_get.assert_called_once_with('ADDR', 'DMM')
        mock_instr.measure_voltage.assert_called_once()

def test_cli_dashboard():
    """Test that the dashboard command launches and stops the dashboard on Ctrl+C."""
    mock_handle = MagicMock()

    with patch('instrumation.dashboard.launch_dashboard') as mock_launch:
        mock_launch.return_value = mock_handle
        with patch('time.sleep', side_effect=KeyboardInterrupt):
            with patch.object(sys, 'argv', ['instrumation', 'dashboard']):
                main()

        mock_launch.assert_called_once_with(http_port=8080, ws_port=8765, udp_port=9999)
        mock_handle.stop.assert_called_once()
