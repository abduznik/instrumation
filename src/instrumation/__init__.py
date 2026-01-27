from .scanner import scan
from .device import UUTHandler
import pyvisa
from .drivers.keysight import KeysightMXA
from .drivers.rigol import RigolDSA

# Global storage for the last found devices to help with auto-connect
_discovered_devices = []

def search_devices():
    """
    Returns a user-friendly list of available devices.
    """
    global _discovered_devices
    _discovered_devices = scan()
    
    print(f"Found {len(_discovered_devices)} devices:")
    for i, dev in enumerate(_discovered_devices):
        print(f"[{i}] {dev['id']} ({dev['desc']})")
    
    return _discovered_devices

def connect(serial_id=None, visa_id=None):
    """
    Creates the connection object for the full test station (Serial + VISA).
    """
    global _discovered_devices
    
    if not _discovered_devices and (serial_id is None or visa_id is None):
        search_devices()

    if serial_id is None:
        for dev in _discovered_devices:
            if dev['type'] == 'serial':
                serial_id = dev['id']
                break 
    
    if visa_id is None:
        for dev in _discovered_devices:
            if dev['type'] == 'visa':
                visa_id = dev['id']
                break 
    
    return UUTHandler(serial_port=serial_id, visa_address=visa_id)

def connect_instrument(visa_address):
    """
    Smart Factory: Connects to a specific instrument and loads the correct driver.
    """
    rm = pyvisa.ResourceManager()
    try:
        resource = rm.open_resource(visa_address)
    except Exception as e:
        raise ConnectionError(f"Could not open resource {visa_address}: {e}")
    
    # 1. Ask the device what it is
    try:
        idn_string = resource.query("*IDN?").strip()
        print(f"Detected Hardware: {idn_string}")
    except Exception as e:
         print(f"Error querying IDN: {e}")
         idn_string = "Unknown"

    # 2. Decide which driver to load based on the response
    if "Keysight" in idn_string or "Agilent" in idn_string:
        return KeysightMXA(resource)
    
    elif "Rigol" in idn_string:
        return RigolDSA(resource)
    
    else:
        # Fallback or error
        # For now, if we can't identify, we might return a generic wrapper or raise error
        # Letting the user know is best.
        print(f"Warning: Unknown device '{idn_string}'. No specific driver found.")
        # We could return a generic SpectrumAnalyzer if we had a concrete one, 
        # but for now let's raise or return None
        raise ValueError(f"Unknown device: {idn_string}. No driver found.")
