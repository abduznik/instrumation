import pytest
from unittest.mock import patch, MagicMock
from instrumation.cli import main
import sys

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
