import os

def is_sim_mode() -> bool:
    """
    Checks the INSTRUMATION_MODE environment variable.
    Returns True if set to 'SIM', else False.
    """
    return os.environ.get("INSTRUMATION_MODE", "").upper() == "SIM"

def get_config():
    """
    Returns the default configuration dictionary.
    In a real app, this might load from a JSON/YAML file.
    """
    return {
        "visa_address": os.environ.get("VISA_ADDRESS", "USB0::0x2A8D::0x1301::MY54400000::0::INSTR"),
        "serial_port": os.environ.get("SERIAL_PORT", "COM3"),
        "instrument_type": os.environ.get("INSTRUMENT_TYPE", "DMM"),
        "log_file": "test_report.csv"
    }
