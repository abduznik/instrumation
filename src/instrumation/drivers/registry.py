import logging
from typing import Dict, Type, List, Optional
from .base import InstrumentDriver

logger = logging.getLogger(__name__)

class DriverRegistry:
    """Registry to keep track of available instrument drivers."""
    
    # Map of type -> list of driver classes
    _drivers: Dict[str, List[Type[InstrumentDriver]]] = {}

    @classmethod
    def register(cls, driver_type: str):
        """Decorator to register a driver class.
        
        Args:
            driver_type (str): The category of the driver (e.g., 'DMM', 'SA').
        """
        def decorator(driver_cls: Type[InstrumentDriver]):
            if driver_type not in cls._drivers:
                cls._drivers[driver_type] = []
            
            if driver_cls not in cls._drivers[driver_type]:
                cls._drivers[driver_type].append(driver_cls)
                logger.debug(f"Registered driver: {driver_cls.__name__} for type {driver_type}")
            
            return driver_cls
        return decorator

    @classmethod
    def get_drivers_by_type(cls, driver_type: str) -> List[Type[InstrumentDriver]]:
        """Returns all registered drivers for a specific type."""
        return cls._drivers.get(driver_type, [])

    @classmethod
    def find_driver(cls, driver_type: str, class_name: str) -> Optional[Type[InstrumentDriver]]:
        """Finds a specific driver class by name."""
        for drv in cls.get_drivers_by_type(driver_type):
            if drv.__name__ == class_name:
                return drv
        return None

register_driver = DriverRegistry.register
