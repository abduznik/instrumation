import pyvisa
import logging
import os
import time
from .drivers.real import RealDriver
from .drivers.registry import DriverRegistry
from .drivers.base import Oscilloscope, SpectrumAnalyzer, SignalGenerator, FunctionGenerator, PowerSupply, Multimeter, NetworkAnalyzer

logger = logging.getLogger(__name__)

# Global Resource Manager to prevent "Too many managers" errors on macOS
_GLOBAL_RM = None

def get_rm():
    global _GLOBAL_RM
    if _GLOBAL_RM is None:
        ni_lib = "/Library/Frameworks/VISA.framework/VISA"
        rm_args = ni_lib if os.path.exists(ni_lib) else None
        _GLOBAL_RM = pyvisa.ResourceManager(rm_args)
    return _GLOBAL_RM

def is_sim_mode() -> bool:
    return os.environ.get("INSTRUMATION_MODE", "REAL").upper() == "SIM"

def _discover_lan_resources() -> list:
    """Scans the local ARP table for potential LAN instruments."""
    resources = []
    try:
        import subprocess
        import re
        output = subprocess.check_output(["arp", "-an"]).decode()
        ips = re.findall(r"\((\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\)", output)
        for ip in ips:
            # Skip broadcast and local loopback
            if ip.endswith(".255") or ip.startswith("127.") or ip.startswith("224.") or ip.startswith("239."):
                continue
            # Try both VXI-11 and HiSLIP — modern Keysight instruments prefer HiSLIP
            resources.append(f"TCPIP::{ip}::hislip0::INSTR")
            resources.append(f"TCPIP::{ip}::INSTR")
    except Exception:
        pass
    return resources

def _discover_mdns_resources() -> list:
    """Probe known Keysight mDNS hostnames via HiSLIP."""
    import socket
    resources = []
    # Common Keysight hostname patterns resolvable via mDNS/Bonjour
    candidates = [
        "a-n5232a-20127.local",  # your VNA
        "a-n9030a-10156.local",  # your PXA
    ]
    for host in candidates:
        try:
            # Resolve and check if HiSLIP port (4880) is open
            socket.getaddrinfo(host, 4880)
            resources.append(f"TCPIP::{host}::hislip0::INSTR")
        except socket.gaierror:
            pass
    return resources

def get_instrument(resource_address: str, driver_type: str = "GENERIC") -> any:
    # 0. Check for replay mode (Highest Priority)
    if resource_address.startswith("replay://"):
        file_path = resource_address.replace("replay://", "")
        from .drivers.replay import ReplayDriver
        return ReplayDriver(resource_address, master_file=file_path)

    # 1. Handle Simulation Mode (The Digital Twin Path)
    if is_sim_mode():
        from .drivers.simulated import SimulatedMultimeter
        drivers = DriverRegistry.get_drivers_by_type(driver_type)
        for drv_cls in drivers:
            if "Simulated" in drv_cls.__name__:
                # Use the requested address or a mock one
                addr = resource_address if resource_address != "AUTO" else "USB0::SIM::INSTR"
                drv = drv_cls(addr)
                drv.connect()
                return drv
        
        # If explicitly requested a type and not found, raise error (don't fallback to DMM silently)
        if driver_type != "GENERIC":
            raise ValueError(f"No simulated driver found for type: {driver_type}")

        # Fallback for GENERIC only
        drv = SimulatedMultimeter(resource_address if resource_address != "AUTO" else "USB0::SIM::INSTR")
        drv.connect()
        return drv

    # 2. Handle AUTO discovery
    if resource_address == "AUTO":
        import json
        from concurrent.futures import ThreadPoolExecutor, as_completed
        cache_file = ".visa_cache.json"
        
        # 1. Load Cache & LAN (The Fast Resources)
        cached_resources = []
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    cached_resources = json.load(f)
            except (IOError, OSError, json.JSONDecodeError):
                pass
        
        lan_resources = _discover_lan_resources()
        tried = set()

        def run_probe(resources, desc):
            # Sort by priority and recency
            candidates = []
            for r in resources:
                if r not in tried:
                    candidates.append(r)
            
            if not candidates:
                return None
            
            # Sort: Priority first, then preserve order (recency)
            candidates.sort(key=lambda x: "ASRL5" in x or "TCPIP" in x or "USB0" in x, reverse=True)
            
            logger.info(f"AUTO-Discovery checking {desc}: {candidates}")
            
            if len(candidates) <= 2:
                for res in candidates:
                    tried.add(res)
                    result = probe_resource(res)
                    if result:
                        update_cache(result.resource_address)
                        return result
                return None

            with ThreadPoolExecutor(max_workers=4) as executor:
                future_to_res = {executor.submit(probe_resource, res): res for res in candidates}
                for future in as_completed(future_to_res):
                    tried.add(future_to_res[future])
                    result = future.result()
                    if result:
                        update_cache(result.resource_address)
                        return result
            return None

        def update_cache(res):
            try:
                # Move successful resource to the front of the cache
                new_cache = [res] + [r for r in cached_resources if r != res]
                with open(cache_file, "w") as f:
                    json.dump(new_cache[:10], f) # Keep top 10 for speed
            except (IOError, OSError):
                pass

        def probe_resource(res):
            try:
                if "ASRL" in res and any(p in res for p in ["1", "2", "3", "4"]):
                    return None
                dev = get_instrument(res, driver_type)
                type_map = {"SCOPE": Oscilloscope, "SA": SpectrumAnalyzer, "SG": (SignalGenerator, FunctionGenerator), "PSU": PowerSupply, "DMM": Multimeter, "VNA": NetworkAnalyzer, "NA": NetworkAnalyzer}
                if driver_type == "GENERIC" or (type_map.get(driver_type) and isinstance(dev, type_map.get(driver_type))):
                    return dev
                dev.disconnect()
            except Exception:
                pass
            return None

        # --- Phase 0: Try ONLY Cache (Super Fast) ---
        if cached_resources:
            result = run_probe(cached_resources, "Super Fast (Cache Only)")
            if result:
                return result

        # --- Phase 0.5: Try mDNS (Bonjour) ---
        mdns_resources = _discover_mdns_resources()
        result = run_probe(mdns_resources, "mDNS/Bonjour")
        if result:
            return result

        # --- Phase 1: Try LAN (Quick Search) ---
        result = run_probe(lan_resources, "Fast Track (LAN)")
        if result:
            return result

        # --- Phase 2: Try Full VISA Scan (The 10s Tax) ---
        rm = get_rm()
        visa_resources = list(rm.list_resources())
        result = run_probe(visa_resources, "Slow Track (Full Scan)")
        if result:
            return result
        
        raise ValueError(f"AUTO-Discovery could not find a suitable {driver_type} instrument.")

    # 4. Real Hardware Logic
    idn = ""
    try:
        if "SIM" in resource_address or "MOCK" in resource_address:
            idn = ""
        else:
            base_dev = RealDriver(resource_address, rm=get_rm())
            
            # Smart Probe for Serial Ports (like TDK-Lambda)
            if "ASRL" in resource_address:
                try:
                    base_dev.inst = base_dev.rm.open_resource(resource_address)
                    base_dev.inst.baud_rate = 9600
                    base_dev.inst.read_termination = '\r\n'
                    base_dev.inst.write_termination = '\r\n'
                    base_dev.inst.timeout = 500 # 500ms is enough for local Serial
                    base_dev.inst.write('INST:NSEL 6')
                    time.sleep(0.2)
                    idn = base_dev.inst.query("*IDN?").upper()
                    base_dev.inst.close()
                except Exception:
                    pass
            
            if not idn:
                base_dev.connect()
                # Set a safer timeout for the ID query during discovery
                base_dev.inst.timeout = 2000
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
    elif "KEYSIGHT" in idn or "AGILENT" in idn or "HEWLETT-PACKARD" in idn or "HP" in idn:
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
        elif "E83" in idn or "N52" in idn or "PNA" in idn:
            from .drivers.keysight import KeysightPNA
            final_drv = KeysightPNA(resource_address)
    elif "SIGLENT" in idn:
        from .drivers.siglent import SiglentSDS
        final_drv = SiglentSDS(resource_address)
    elif "TDK-LAMBDA" in idn or "Z+" in idn:
        from .drivers.tdk import TDKLambdaZPlus
        final_drv = TDKLambdaZPlus(resource_address)

    if not final_drv:
        drivers = DriverRegistry.get_drivers_by_type(driver_type)
        for drv_cls in drivers:
            if "Simulated" not in drv_cls.__name__:
                final_drv = drv_cls(resource_address)
                break
    if not final_drv:
        final_drv = RealDriver(resource_address, rm=get_rm())


    final_drv.connect()
    
    # Update cache with successful manual connection to enable future AUTO discovery
    if resource_address != "AUTO":
        try:
            cache_file = ".visa_cache.json"
            cached_resources = []
            if os.path.exists(cache_file):
                with open(cache_file, "r") as f:
                    cached_resources = json.load(f)
            new_cache = [resource_address] + [r for r in cached_resources if r != resource_address]
            with open(cache_file, "w") as f:
                json.dump(new_cache[:10], f)
        except Exception:
            pass

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