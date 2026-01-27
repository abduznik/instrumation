import pyvisa
import serial
import time

class VisaDriver:
    """Generic wrapper for VISA instruments."""
    def __init__(self, address, timeout=5000):
        self.rm = pyvisa.ResourceManager()
        self.address = address
        try:
            self.inst = self.rm.open_resource(address)
            self.inst.timeout = timeout
            self.inst.write("*CLS")
        except Exception as e:
            print(f"Error connecting to {address}: {e}")
            self.inst = None

    def query_value(self, command):
        if self.inst:
            try:
                return self.inst.query(command).strip()
            except Exception as e:
                print(f"VISA Query Error: {e}")
                return 0.0
        return 0.0

    def write(self, command):
        if self.inst:
            self.inst.write(command)

    def close(self):
        if self.inst:
            self.inst.close()
            self.rm.close()

class SerialDriver:
    """Generic wrapper for Serial devices."""
    def __init__(self, port, baudrate=9600, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        try:
            self.ser = serial.Serial(port, baudrate, timeout=timeout)
            time.sleep(2) # Stabilization time
        except Exception as e:
            print(f"Error opening serial port {port}: {e}")
            self.ser = None

    def send_command(self, command_str):
        if self.ser:
            try:
                # Handle both bytes and string input
                if isinstance(command_str, str):
                    data = command_str.encode('utf-8')
                    if not command_str.endswith('\n'):
                         data += b'\n'
                else:
                    data = command_str
                
                self.ser.write(data)
            except Exception as e:
                print(f"Serial Write Error: {e}")

    def read_response(self):
        if self.ser:
            try:
                return self.ser.readline().decode('utf-8').strip()
            except Exception:
                return ""
        return ""

    def close(self):
        if self.ser:
            self.ser.close()