from .scanner import scan
from .device import UUTHandler
from .station import Station
from .utils import DataBroadcaster
from .factory import get_instrument, get_instrument_from_config
import pyvisa

__all__ = ["scan", "UUTHandler", "Station", "DataBroadcaster", "get_instrument", "get_instrument_from_config"]

# Global storage for the last found devices to help with auto-connect
_discovered_devices = []

def search_devices():
    """Returns a user-friendly list of available devices."""
    global _discovered_devices
    _discovered_devices = scan()
    
    print(f"Found {len(_discovered_devices)} devices:")
    for i, dev in enumerate(_discovered_devices):
        print(f"[{i}] {dev['id']} ({dev['desc']})")
    
    return _discovered_devices

def connect(serial_id=None, visa_id=None):
    """Creates the connection object for the full test station (Serial + VISA)."""
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

def connect_instrument(visa_address: str, driver_type: str = None):
    """Smart Factory: Connects to a specific instrument and loads the correct driver.
    
    If driver_type is None, it attempts to detect the hardware via *IDN?.
    """
    if driver_type:
        return get_instrument(visa_address, driver_type)
        
    # Auto-detection logic
    try:
        rm = pyvisa.ResourceManager()
        resource = rm.open_resource(visa_address)
        idn = resource.query("*IDN?").upper()
        resource.close()
        
        if "KEYSIGHT" in idn or "AGILENT" in idn:
            if "MXA" in idn:
                return get_instrument(visa_address, "SA")
            if "EXG" in idn or "MXG" in idn:
                return get_instrument(visa_address, "SG")
            return get_instrument(visa_address, "SG")
        if "SIGLENT" in idn:
            return get_instrument(visa_address, "SCOPE")
        if "RIGOL" in idn:
            return get_instrument(visa_address, "SA")
        if "TEKTRONIX" in idn:
            return get_instrument(visa_address, "SCOPE")
        if "ROHDE" in idn:
            return get_instrument(visa_address, "SG")
    except Exception:
        pass
        
    return get_instrument(visa_address, "DMM") # Fallback
