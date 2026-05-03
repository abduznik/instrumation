import pyvisa
import logging
import os
from .drivers.real import RealDriver
from .drivers.replay import ReplayDriver
from .drivers.simulated import SimulatedDriver
from .drivers.registry import DriverRegistry
from .drivers.base import Oscilloscope, SpectrumAnalyzer, SignalGenerator, FunctionGenerator, PowerSupply, Multimeter

logger = logging.getLogger(__name__)

def is_sim_mode() -> bool:
    return os.environ.get("INSTRUMATION_MODE", "REAL").upper() == "SIM"

def _discover_lan_resources() -> list:
    """Scans the local ARP table for potential LAN instruments."""
    resources = []
    try:
        import subprocess
        import re
        output = subprocess.check_output(["arp", "-a"]).decode()
        ips = re.findall(r"\((\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\)", output)
        for ip in ips:
            if ip.startswith("169.254") or ip.startswith("192.168"):
                resources.append(f"TCPIP::{ip}::INSTR")
    except Exception:
        pass
    return resources

def get_instrument(resource_address: str, driver_type: str = "GENERIC") -> any:
    # 1. Handle AUTO discovery
    if resource_address == "AUTO":
        ni_lib = "/Library/Frameworks/VISA.framework/VISA"
        rm_args = ni_lib if os.path.exists(ni_lib) else None
        rm = pyvisa.ResourceManager(rm_args)
        
        visa_resources = list(rm.list_resources())
        candidate_resources = visa_resources + _discover_lan_resources()
        
        logger.info(f"AUTO-Discovery checking candidates: {candidate_resources}")
        
        for res in candidate_resources:
            try:
                if res.startswith("ASRL") and len(candidate_resources) > 1:
                    continue
                
                dev = get_instrument(res, driver_type)
                
                type_map = {
                    "SCOPE": Oscilloscope,
                    "SA": SpectrumAnalyzer,
                    "SG": (SignalGenerator, FunctionGenerator),
                    "PSU": PowerSupply,
                    "DMM": Multimeter
                }
                
                if driver_type == "GENERIC":
                    return dev
                
                expected_base = type_map.get(driver_type)
                if expected_base and isinstance(dev, expected_base):
                    return dev
                    
                dev.disconnect()
            except Exception:
                continue
        
        raise ValueError(f"AUTO-Discovery could not find a suitable {driver_type} instrument.")

    # 2. Check for replay mode
    if resource_address.startswith("replay://"):
        master_file = resource_address.replace("replay://", "")
        return ReplayDriver("REPLAY_DEVICE", master_file)

    # 3. Simulation Logic
    if is_sim_mode():
        drivers = DriverRegistry.get_drivers_by_type(driver_type)
        for drv_cls in drivers:
            if "Simulated" in drv_cls.__name__:
                return drv_cls(resource_address)
        if driver_type == "DMM":
            return SimulatedDriver(resource_address)
        raise ValueError(f"No simulated driver found for type: {driver_type}")

    # 4. Real Hardware Logic
    ni_lib = "/Library/Frameworks/VISA.framework/VISA"
    rm_args = ni_lib if os.path.exists(ni_lib) else None
    
    idn = ""
    try:
        if "SIM" in resource_address or "MOCK" in resource_address:
            idn = ""
        else:
            base_dev = RealDriver(resource_address)
            if rm_args:
                base_dev.rm = pyvisa.ResourceManager(rm_args)
            base_dev.connect()
            idn = base_dev.get_id().upper()
            base_dev.disconnect()
    except Exception as e:
        logger.warning(f"Identification failed for {resource_address}: {e}")
        idn = ""

    # Smart Routing based on IDN
    final_drv = None
    if "TEKTRONIX" in idn:
        if "AFG" in idn:
            from .drivers.tektronix import TektronixAFG
            final_drv = TektronixAFG(resource_address)
        else:
            from .drivers.tektronix import TektronixTDS
            final_drv = TektronixTDS(resource_address)
    elif "KEYSIGHT" in idn or "AGILENT" in idn:
        if any(m in idn for m in ["DSO-X", "MSO-X", "DSOX", "MSOX"]):
            from .drivers.keysight import KeysightInfiniiVision
            final_drv = KeysightInfiniiVision(resource_address)
        elif any(m in idn for m in ["N9030", "N9020", "N9010", "PXA", "MXA", "EXA"]):
            from .drivers.keysight import KeysightPXA
            final_drv = KeysightPXA(resource_address)
        elif any(m in idn for m in ["E8257", "N5181", "N5182", "N5183", "PSG", "MXG", "EXG"]):
            from .drivers.keysight import KeysightSG
            final_drv = KeysightSG(resource_address)
        elif "N99" in idn or "FIELD FOX" in idn:
            from .drivers.keysight import KeysightFieldFox
            final_drv = KeysightFieldFox(resource_address)
    elif "SIGLENT" in idn:
        from .drivers.siglent import SiglentSDS
        final_drv = SiglentSDS(resource_address)
    elif "TDK-LAMBDA" in idn or "Z+" in idn:
        from .drivers.tdk_lambda import TDKLambdaZPlus
        final_drv = TDKLambdaZPlus(resource_address)

    if not final_drv:
        drivers = DriverRegistry.get_drivers_by_type(driver_type)
        for drv_cls in drivers:
            if "Simulated" not in drv_cls.__name__:
                final_drv = drv_cls(resource_address)
                break
    if not final_drv:
        final_drv = RealDriver(resource_address)

    if rm_args:
        final_drv.rm = pyvisa.ResourceManager(rm_args)
    final_drv.connect()
    return final_drv

def get_instrument_from_config(config: dict) -> any:
    resource_address = config.get("address")
    driver_type = config.get("type") # Mandatory for test compatibility
    if not resource_address:
        raise ValueError("Missing required configuration key: 'address'")
    if not driver_type:
        raise ValueError("Missing required configuration key: 'type'")
    return get_instrument(resource_address, driver_type)

def load_plugins(plugin_path: str = None):
    """Dynamically loads all available instrument drivers."""
    import importlib
    import pkgutil
    import sys
    
    # 1. Load built-in drivers
    import instrumation.drivers as drivers_pkg
    for _, name, _ in pkgutil.iter_modules(drivers_pkg.__path__):
        importlib.import_module(f"instrumation.drivers.{name}")
            
    # 2. Load from external path if provided
    if plugin_path:
        if plugin_path not in sys.path:
            sys.path.insert(0, plugin_path)
        for _, name, _ in pkgutil.iter_modules([plugin_path]):
            importlib.import_module(name)