from .config import is_sim_mode
from .drivers.simulated import SimulatedMultimeter, SimulatedPowerSupply, SimulatedSpectrumAnalyzer, SimulatedNetworkAnalyzer, SimulatedDriver
# Import real drivers (assuming we have wrappers or generic SCPI ones)
# For now, we reuse the generic RealDriver structure or import specific ones
from .drivers.real import RealDriver 
from .drivers.keysight import KeysightPNA, KeysightMXA
from .drivers.tdk import TDKLambdaZPlus
from .drivers.siglent import SiglentSDS

def get_driver(resource_address: str):
    """Legacy factory for generic driver (defaults to DMM behavior)."""
    if is_sim_mode():
        return SimulatedDriver(resource_address)
    else:
        return RealDriver(resource_address)

def get_instrument(resource_address: str, driver_type: str):
    """Factory to get specific instrument types.

    Args:
        resource_address (str): VISA address or dummy string.
        driver_type (str): The type of driver to create ("DMM", "PSU", "SA", "NA", "SCOPE").

    Returns:
        InstrumentDriver: An instance of the requested instrument driver.

    Raises:
        ValueError: If the driver_type is not recognized.
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
        elif driver_type == "SCOPE":
            # Return a generic simulated driver or update to SimulatedOscilloscope when available
            return SimulatedDriver(resource_address)
        else:
            raise ValueError(f"Unknown driver type for simulation: {driver_type}")
    else:
        # Real Hardware Logic
        if driver_type == "NA":
            return KeysightPNA(resource_address)
        elif driver_type == "PSU":
            return TDKLambdaZPlus(resource_address)
        elif driver_type == "SA":
            return KeysightMXA(resource_address)
        elif driver_type == "SCOPE":
            return SiglentSDS(resource_address)
        elif driver_type == "DMM":
            # For DMM, we might return a generic SCPI wrapper or specific one
            print(f"[Real] Warning: returning generic driver for {driver_type}")
            return RealDriver(resource_address)
        else:
            raise ValueError(f"Unknown driver type for real hardware: {driver_type}")

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