from .config import is_sim_mode
from .drivers.simulated import SimulatedMultimeter, SimulatedPowerSupply, SimulatedSpectrumAnalyzer, SimulatedNetworkAnalyzer, SimulatedDriver
# Import real drivers (assuming we have wrappers or generic SCPI ones)
# For now, we reuse the generic RealDriver structure or import specific ones
from .drivers.real import RealDriver 
from .drivers.keysight import KeysightPNA, KeysightMXA
from .drivers.tdk import TDKLambdaZPlus

def get_driver(resource_address: str):
    """Legacy factory for generic driver (defaults to DMM behavior)."""
    if is_sim_mode():
        return SimulatedDriver(resource_address)
    else:
        return RealDriver(resource_address)

def get_instrument(resource_address: str, driver_type: str):
    """
    Factory to get specific instrument types.
    
    Args:
        resource_address: VISA address or dummy string
        driver_type: "DMM", "PSU", "SA", "NA"
    """
    if is_sim_mode():
        if driver_type == "DMM":
            return SimulatedMultimeter(resource_address)
        elif driver_type == "PSU":
            return SimulatedPowerSupply(resource_address)
        elif driver_type == "SA":
            return SimulatedSpectrumAnalyzer(resource_address)
        elif driver_type == "NA":
            return SimulatedNetworkAnalyzer(resource_address)
        else:
            raise ValueError(f"Unknown driver type: {driver_type}")
    else:
        # Real Hardware Logic (Placeholder)
        if driver_type == "NA":
            return KeysightPNA(resource_address)
        elif driver_type == "PSU":
            return TDKLambdaZPlus(resource_address)
        elif driver_type == "SA":
            return KeysightMXA(resource_address)
        
        # In a real scenario, we might return a generic SCPI wrapper 
        # or use auto-detection (like connect_instrument logic)
        # For this example, we return the generic RealDriver 
        # but in a real app, we'd wrap it in the correct class.
        print(f"[Real] Warning: returning generic driver for {driver_type}")
        return RealDriver(resource_address)
