from .config import is_sim_mode
from .drivers.simulated import SimulatedMultimeter, SimulatedPowerSupply, SimulatedSpectrumAnalyzer, SimulatedNetworkAnalyzer, SimulatedOscilloscope, SimulatedDriver
# Import real drivers (assuming we have wrappers or generic SCPI ones)
# For now, we reuse the generic RealDriver structure or import specific ones
from .drivers.real import RealDriver 
from .drivers.keysight import KeysightPNA, KeysightMXA
from .drivers.tdk import TDKLambdaZPlus
from .drivers.siglent import SiglentSDS
from .drivers.rs import RohdeSchwarzSG, RohdeSchwarzSA
from .drivers.anritsu import AnritsuSA, AnritsuVNA
from .drivers.registry import DriverRegistry
from .drivers.replay import ReplayDriver
import importlib.util
import sys
import os
import logging
from .scanner import scan

logger = logging.getLogger(__name__)

def get_driver(resource_address: str):
    """Legacy factory for generic driver (defaults to DMM behavior).
    
    .. deprecated:: 0.1.7
       Use :func:`get_instrument` instead.
    """
    import warnings
    warnings.warn("get_driver is deprecated, use get_instrument(address, 'DMM') instead", DeprecationWarning, stacklevel=2)
    return get_instrument(resource_address, "DMM")

def get_instrument(resource_address: str, driver_type: str):
    """Factory to get specific instrument types.

    Args:
        resource_address (str): VISA address or dummy string.
        driver_type (str): The type of driver to create ("DMM", "PSU", "SA", "NA", "SCOPE").

    Returns:
        InstrumentDriver: An instance of the requested instrument driver.

    Raises:
        ValueError: If the driver_type is not recognized or no driver is found.
    """
    # 1. Ensure plugins are loaded
    # (Optional: we could call this once at module level or on demand)
    
    # Normalize aliases
    if driver_type.upper() == "VNA":
        driver_type = "NA"
    
    drivers = DriverRegistry.get_drivers_by_type(driver_type)
    
    # 2. Handle AUTO address
    if resource_address == "AUTO":
        logger.info(f"AUTO address specified for {driver_type}. Scanning...")
        devices = scan()
        visa_devices = [d['id'] for d in devices if d['type'] == 'visa']
        
        if not visa_devices:
            raise ValueError(f"AUTO address specified but no VISA instruments found for type: {driver_type}")
        
        # Sort candidates: Prioritize TCPIP and USB over ASRL/GPIB
        def resource_priority(res: str) -> int:
            if res.startswith("TCPIP"): return 0
            if res.startswith("USB"): return 1
            if res.startswith("GPIB"): return 2
            return 3 # ASRL etc.

        visa_devices.sort(key=resource_priority)
        
        # Filter out system serial ports (ASRL) if we have better candidates
        real_instruments = [d for d in visa_devices if not d.startswith("ASRL")]
        if real_instruments:
            resource_address = real_instruments[0]
        else:
            resource_address = visa_devices[0]
            
        logger.info(f"AUTO: Resolved to {resource_address}")
        print(f"AUTO: Resolved to {resource_address}")

    # 3. Check for replay mode (address starts with 'replay://')
    if resource_address.startswith("replay://"):
        master_file = resource_address.replace("replay://", "")
        return ReplayDriver("REPLAY_DEVICE", master_file)

    if is_sim_mode():
        # Find a simulated driver for this type
        for drv_cls in drivers:
            if "Simulated" in drv_cls.__name__:
                return drv_cls(resource_address)
        
        # Fallback to SimulatedDriver alias if it exists and matches
        if driver_type == "DMM":
             return SimulatedDriver(resource_address)
             
        raise ValueError(f"No simulated driver found for type: {driver_type}")
    else:
        # Real Hardware Logic
        # 1. First, establish a basic connection to identify the instrument
        try:
            base_dev = RealDriver(resource_address)
            idn = base_dev.get_id().upper()
            base_dev.close() # Close temp connection
        except Exception as e:
            logger.warning(f"Could not query *IDN? from {resource_address}: {e}")
            idn = ""

        # 2. Smart Routing based on IDN
        if "ANRITSU" in idn:
            if "MS203" in idn: # MS2035B/MS2034B
                from .drivers.anritsu import AnritsuMS2035B
                return AnritsuMS2035B(resource_address)
            if "MS465" in idn: # ShockLine
                from .drivers.anritsu import AnritsuShockLineVNA
                return AnritsuShockLineVNA(resource_address)
        
        if "FIELD FOX" in idn or "N99" in idn: # N99xx Series
            from .drivers.keysight import KeysightFieldFox
            return KeysightFieldFox(resource_address)

        # 3. Fallback to registry-based selection
        for drv_cls in drivers:
            if "Simulated" not in drv_cls.__name__:
                return drv_cls(resource_address)
        
        # Legacy fallback for DMM
        if driver_type == "DMM":
            print(f"[Real] Warning: returning generic driver for {driver_type}")
            return RealDriver(resource_address)
            
        raise ValueError(f"No real driver found for type: {driver_type}")

def load_plugins(plugin_dir: str = "plugins"):
    """Loads all drivers from the specified plugins directory.
    
    Args:
        plugin_dir (str): Path to the directory containing plugin .py files.
    """
    if not os.path.exists(plugin_dir):
        return

    for filename in os.listdir(plugin_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            file_path = os.path.join(plugin_dir, filename)
            
            try:
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    logger.info(f"Loaded plugin: {module_name}")
            except Exception as e:
                logger.error(f"Failed to load plugin {module_name} from {file_path}: {e}")

def get_instrument_from_config(config: dict):
    """Creates an instrument driver from a configuration dictionary.

    The configuration dictionary must contain 'address' and 'type' keys.

    Args:
        config (dict): Configuration dictionary containing 'address' and 'type'.

    Returns:
        InstrumentDriver: An instance of the requested instrument driver.

    Raises:
        ValueError: If 'address' or 'type' keys are missing, or if the driver type is unrecognized.
    """
    required_keys = ["address", "type"]
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required configuration key: '{key}'")

    return get_instrument(config["address"], config["type"])