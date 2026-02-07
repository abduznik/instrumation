import time
from .transport import VisaDriver, SerialDriver

class UUTHandler:
    """The main object the user interacts with.

    It manages the connection to the specific UUT.

    Attributes:
        box (SerialDriver): Driver for the serial connection to the multiplexer/box.
        inst (VisaDriver): Driver for the VISA instrument connection.
    """
    def __init__(self, serial_port, visa_address):
        """Initializes the UUTHandler.

        We assume the user needs BOTH to test a UUT properly.

        Args:
            serial_port (str): The serial port for the box (e.g., 'COM3').
            visa_address (str): The VISA address for the instrument (e.g., 'GPIB0::1::INSTR').
        """
        self.box = SerialDriver(serial_port)
        self.inst = VisaDriver(visa_address)
        print(f"Connected to UUT System on {serial_port} & {visa_address}")

    def mes_voltage(self, port_number):
        """User command: Measures voltage on a specific UUT port.

        Args:
            port_number (int): The port number on the multiplexer to switch to.

        Returns:
            float: The measured voltage in Volts. Returns 0.0 if value conversion fails.
        """
        # 1. Switch the Multiplexer/Box to the correct port
        print(f"Switching Relay to Port {port_number}...")
        self.box.send_command(f"RELAY:CH{port_number}")
        time.sleep(0.5) # Wait for relay to settle

        # 2. Measure with the Instrument
        # If no instrument connected (simulation), return a dummy value
        if not self.inst.inst:
             print("Warning: No Instrument connected. Returning simulation value.")
             return 3.3

        val_str = self.inst.query_value("MEAS:VOLT:DC?")
        try:
            return float(val_str)
        except ValueError:
            return 0.0

    def close(self):
        """Closes connections to both the box and the instrument."""
        self.box.close()
        self.inst.close()