import os
import toml
from .factory import get_instrument

class Station:
    """Station manager that loads instrument configurations from TOML.

    Attributes are dynamically attached to the station object based on the TOML configuration,
    allowing for dotted notation access (e.g., station.sa_main).
    """

    RESERVED_NAMES = {
        "load", "close", "connect", "disconnect", "instruments", 
        "config", "address", "type", "resource", "connected"
    }

    def __init__(self, config_path="station.toml"):
        """Initializes the Station by loading the configuration.

        Args:
            config_path (str): Path to the TOML configuration file.
        """
        self.config_path = config_path
        self.instruments = {}
        self.load()

    def load(self):
        """Loads or reloads the configuration from the TOML file."""
        if not os.path.exists(self.config_path):
            print(f"Warning: Configuration file '{self.config_path}' not found. Initializing empty station.")
            return

        try:
            config = toml.load(self.config_path)
        except Exception as e:
            print(f"Error: Failed to parse TOML file '{self.config_path}': {e}")
            return

        instrument_configs = config.get("instruments", {})
        
        for name, settings in instrument_configs.items():
            try:
                self._add_instrument(name, settings)
            except Exception as e:
                print(f"Error: Failed to initialize instrument '{name}': {e}")

    def _add_instrument(self, name, settings):
        """Creates and attaches an instrument driver instance.

        Args:
            name (str): The name to use as attribute.
            settings (dict): Dictionary with 'driver' and 'address' keys.
        """
        driver_type = settings.get("driver")
        address = settings.get("address")

        if not driver_type or not address:
            raise ValueError(f"Instrument '{name}' must have 'driver' and 'address' specified.")

        # Create the instrument instance using the factory
        instance = get_instrument(address, driver_type)

        # Safety check for reserved names
        attr_name = name
        if name.lower() in self.RESERVED_NAMES:
            attr_name = f"inst_{name}"
            print(f"Warning: Name '{name}' is reserved. Renamed attribute to '{attr_name}'.")

        # Attach as attribute
        setattr(self, attr_name, instance)
        self.instruments[name] = instance

    def connect(self):
        """Connects all initialized instruments."""
        for name, inst in self.instruments.items():
            try:
                inst.connect()
                print(f"Connected to {name} at {inst.resource}")
            except Exception as e:
                print(f"Failed to connect to {name}: {e}")

    def disconnect(self):
        """Disconnects all initialized instruments."""
        for name, inst in self.instruments.items():
            try:
                inst.disconnect()
                print(f"Disconnected from {name}")
            except Exception as e:
                print(f"Error disconnecting from {name}: {e}")
