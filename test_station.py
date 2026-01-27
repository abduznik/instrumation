import pyvisa
import serial
import time
import csv
import os
from datetime import datetime

class InstrumentController:
    """Handles VISA instruments (Keysight, Tektronix, etc.)"""
    def __init__(self, resource_manager, address):
        self.inst = resource_manager.open_resource(address)
        # Standard SCPI initialization
        self.inst.timeout = 5000 
        self.inst.write("*CLS") # Clear errors

    def measure_voltage(self):
        """Example: Ask DMM for a reading"""
        return float(self.inst.query("MEAS:VOLT:DC?"))

    def set_frequency(self, freq):
        """Example: Set Signal Generator frequency"""
        self.inst.write(f"FREQ {freq}")

class ControlBox:
    """Handles the custom UART box that controls UUT DC power"""
    def __init__(self, port, baudrate=9600):
        self.ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2) # Wait for serial connection to stabilize

    def set_dc_state(self, state):
        """
        Sends a command to the box to turn DC ON or OFF.
        Adjust the command string ('ON', 'OFF', or Hex) to match your box's protocol.
        """
        command = b'DC_ON\n' if state else b'DC_OFF\n'
        self.ser.write(command)
        # Check for acknowledgement from the box if it sends one
        response = self.ser.readline()
        return response

class UUTTestStation:
    """
    The High-Level API.
    Combines VISA and Serial into one logical unit.
    """
    def __init__(self, visa_address, serial_port, log_file="test_report.csv"):
        self.rm = pyvisa.ResourceManager()
        self.log_file = log_file
        
        print(f"Connecting to Instrument at {visa_address}...")
        self.instrument = InstrumentController(self.rm, visa_address)
        
        print(f"Connecting to Control Box at {serial_port}...")
        self.box = ControlBox(serial_port)
        
        # Initialize log file with headers if it doesn't exist
        if not os.path.exists(self.log_file):
            with open(self.log_file, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Test Name", "Voltage", "Result"])

    def log_result(self, test_name, voltage, result):
        """Logs the test result to a CSV file."""
        with open(self.log_file, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().isoformat(), test_name, voltage, result])
        print(f"Result logged to {self.log_file}")

    def run_power_efficiency_test(self):
        """
        A complex sequence that uses both interfaces.
        """
        print("Starting Test...")
        test_name = "Power Efficiency"
        result = "FAIL"
        
        # 1. Use UART to turn on the UUT
        self.box.set_dc_state(True)
        time.sleep(1) # Wait for UUT boot
        
        # 2. Use VISA to measure the result
        voltage = self.instrument.measure_voltage()
        print(f"UUT Voltage: {voltage}V")
        
        # 3. Logic based on readings
        if voltage > 3.0:
            print("PASS: Voltage within range.")
            result = "PASS"
        else:
            print("FAIL: Voltage too low!")
            result = "FAIL"

        # 4. Log the result
        self.log_result(test_name, voltage, result)

        # 5. Clean up
        self.box.set_dc_state(False)

    def close(self):
        self.instrument.inst.close()
        self.box.ser.close()
        self.rm.close()

# --- USAGE EXAMPLE ---
# This is how you would use it in your actual test scripts:
if __name__ == "__main__":
    # Replace these with your actual IDs
    VISA_ADDR = 'USB0::0x2A8D::0x1301::MY54400000::0::INSTR' 
    SERIAL_PORT = 'COM3' # On Linux/Termux this might be '/dev/ttyUSB0'

    station = UUTTestStation(VISA_ADDR, SERIAL_PORT)
    
    try:
        station.run_power_efficiency_test()
    finally:
        station.close()