import logging
from .real import RealDriver
from .registry import register_driver

logger = logging.getLogger(__name__)

@register_driver("BRIDGE")
class PrologixDriver(RealDriver):
    """
    Driver for the Prologix GPIB-USB Controller.
    This acts as a bridge to communicate with GPIB instruments via a Serial port.
    """

    def __init__(self, resource_address: str, gpib_address: int = 1):
        # Prologix is a serial device, usually /dev/cu.usbserial...
        super().__init__(resource_address)
        self.gpib_address = gpib_address
        self.timeout = 2.0

    def connect(self):
        """Connects to the Serial bridge and configures it as a Controller."""
        super().connect()
        # Initial Prologix configuration
        self.write("++mode 1")      # Set as Controller
        self.write("++auto 0")      # Disable auto-read
        self.write("++eoi 1")       # Enable EOI
        self.write(f"++addr {self.gpib_address}") # Set target GPIB address
        logger.info(f"Prologix Bridge initialized on {self.resource} for GPIB Address {self.gpib_address}")

    def set_gpib_address(self, address: int):
        """Changes the target instrument address."""
        self.gpib_address = address
        self.write(f"++addr {address}")

    def query(self, command: str) -> str:
        """Sends a command and reads the response using ++read."""
        self.write(command)
        # Prologix needs an explicit read command to pull data from the GPIB bus
        self.write("++read eoi")
        return self.read().strip()

    def write(self, command: str):
        """Sends a raw command to the bridge."""
        if not command.endswith("\n") and not command.startswith("++"):
             command += "\n"
        super().write(command)

    def read(self) -> str:
        """Reads data from the serial buffer."""
        # We override to handle the fact that Prologix returns data via Serial
        return super().read()
