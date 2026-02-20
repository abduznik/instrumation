import os
import logging
from types import SimpleNamespace
from typing import Dict, Any
from dataclasses import dataclass

import toml

from .factory import get_instrument

logger = logging.getLogger(__name__)

@dataclass
class InstrumentConfig:
    driver: str
    address: str

    @classmethod
    def from_dict(cls, name: str, data: dict):
        """Creates an InstrumentConfig from a dictionary with validation."""
        driver = data.get("driver")
        address = data.get("address")
        
        if not driver or not address:
            raise ValueError(f"Instrument '{name}' must have 'driver' and 'address' specified.")
            
        return cls(driver=driver, address=address)

class Station:
    """Station manager that loads instrument configurations from TOML.

    Instruments are accessible via the '.instr' attribute using dotted notation 
    (e.g., station.instr.sa_main), preventing collisions with Station methods.
    """

    def __init__(self, config_path: str = "station.toml"):
        """Initializes the Station by loading the configuration.

        Args:
            config_path (str): Path to the TOML configuration file.
        """
        self.config_path = config_path
        self.instruments: Dict[str, Any] = {}
        self.instr = SimpleNamespace()
        self.load()

    def load(self):
        """Loads or reloads the configuration from the TOML file."""
        if not os.path.exists(self.config_path):
            logger.warning(f"Configuration file '{self.config_path}' not found. Initializing empty station.")
            return

        try:
            raw_config = toml.load(self.config_path)
        except Exception as e:
            logger.error(f"Failed to parse TOML file '{self.config_path}': {e}")
            raise

        instrument_configs_raw = raw_config.get("instruments", {})
        
        # Clear existing instruments if reloading
        self.instruments = {}
        self.instr = SimpleNamespace()

        for name, settings in instrument_configs_raw.items():
            try:
                config = InstrumentConfig.from_dict(name, settings)
                self._add_instrument(name, config)
            except ValueError as e:
                logger.error(f"Configuration error for '{name}': {e}")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize instrument '{name}': {e}")

    def _add_instrument(self, name: str, settings: InstrumentConfig):
        """Creates and attaches an instrument driver instance.

        Args:
            name (str): The name to use as attribute.
            settings (InstrumentConfig): Configuration object.
        """
        # Create the instrument instance using the factory
        instance = get_instrument(settings.address, settings.driver)

        # Attach to the instr namespace
        setattr(self.instr, name, instance)
        self.instruments[name] = instance
        logger.debug(f"Instrument '{name}' added to station.")

    def connect(self):
        """Connects all initialized instruments."""
        for name, inst in self.instruments.items():
            try:
                inst.connect()
                logger.info(f"Connected to {name} at {inst.resource}")
            except Exception as e:
                logger.error(f"Failed to connect to {name}: {e}")
                raise

    def disconnect(self):
        """Disconnects all initialized instruments."""
        for name, inst in self.instruments.items():
            try:
                inst.disconnect()
                logger.info(f"Disconnected from {name}")
            except Exception as e:
                logger.error(f"Error disconnecting from {name}: {e}")
