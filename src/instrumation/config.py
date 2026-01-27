import os

def is_sim_mode() -> bool:
    """
    Checks the INSTRUMATION_MODE environment variable.
    Returns True if set to 'SIM', else False.
    """
    return os.environ.get("INSTRUMATION_MODE", "").upper() == "SIM"
