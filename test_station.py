import time
import csv
import os
from datetime import datetime
from instrumation.factory import get_instrument
from instrumation.transport import SerialDriver
from instrumation.config import get_config

class UUTTestStation:
    """
    The High-Level API.
    Combines Instrument drivers and Serial transport into one logical unit.
    """
    def __init__(self, visa_address, serial_port, instrument_type="DMM", log_file="test_report.csv"):
        self.log_file = log_file
        
        print(f"Connecting to {instrument_type} at {visa_address}...")
        self.instrument = get_instrument(visa_address, instrument_type)
        self.instrument.connect()
        
        print(f"Connecting to Control Box at {serial_port}...")
        self.box = SerialDriver(serial_port)
        
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
        
        # 1. Use Serial to turn on the UUT
        self.box.send_command("DC_ON")
        time.sleep(1) # Wait for UUT boot
        
        # 2. Use the instrument driver to measure the result
        # Note: We assume the instrument is a DMM/Multimeter for this test
        try:
            voltage = self.instrument.measure_voltage()
        except AttributeError:
            print(f"Error: Selected instrument {type(self.instrument).__name__} does not support measure_voltage()")
            voltage = 0.0

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
        self.box.send_command("DC_OFF")

    def close(self):
        self.instrument.disconnect()
        self.box.close()

# --- USAGE EXAMPLE ---
if __name__ == "__main__":
    # Load configuration from config.py
    config = get_config()

    station = UUTTestStation(
        config["visa_address"], 
        config["serial_port"],
        instrument_type=config["instrument_type"],
        log_file=config["log_file"]
    )
    
    try:
        station.run_power_efficiency_test()
    finally:
        station.close()
