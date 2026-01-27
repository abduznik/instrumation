import sys
import time
import os
# Add the src directory to path so we can import the library without installing it
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from instrumation import VISAInstrument, SerialDevice, TestLogger, scan_resources
from instrumation.drivers import InstrumentController # Assuming you might want to subclass this

# 1. Custom Implementation of the Generic Library
class MySpecificTestStation:
    def __init__(self, visa_addr, serial_port):
        self.dmm = VISAInstrument(pyvisa.ResourceManager(), visa_addr)
        self.uut_control = SerialDevice(serial_port, baudrate=9600)
        self.logger = TestLogger("production_run_log.csv")

    def run_test_sequence(self):
        print("--- Starting Production Test ---")
        
        # 1. Initialize UUT
        print("Powering on UUT...")
        self.uut_control.send_command(b"DC_ON\n")
        ack = self.uut_control.read_response()
        print(f"UUT Response: {ack}")
        time.sleep(1)

        # 2. Measurement (Mocked logic if no real VISA inst connected)
        if self.dmm.inst:
            volts = float(self.dmm.query("MEAS:VOLT:DC?"))
        else:
            print("Warning: No DMM connected, simulating measurement.")
            volts = 3.3 # Simulation

        # 3. Validation
        status = "PASS" if 3.0 < volts < 3.6 else "FAIL"
        
        # 4. Logging
        self.logger.log("5V Rail Test", f"{volts}V", status)

        # 5. Shutdown
        self.uut_control.send_command(b"DC_OFF\n")

# --- AUTO-DISCOVERY DEMO ---
if __name__ == "__main__":
    import os
    import pyvisa
    
    # Let's try to Auto-Detect first!
    print("Scanning for devices...")
    devices = scan_resources()
    print("Found:", devices)

    # For this example to work without hardware, we need a serial port.
    # In a real scenario, you'd pick one from 'devices['serial']'.
    # Here, we will launch the Emulator if no real ports are found/specified.
    
    target_port = None
    if devices['serial']:
        target_port = devices['serial'][0]['port']
        print(f"Using found port: {target_port}")
    else:
        print("No serial ports found. Launching Emulator...")
        # Import emulator dynamically just for this demo
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../tests')))
        from uut_emulator import UUTEmulator
        emu = UUTEmulator()
        target_port = emu.get_port()
        # Give the emulator a moment to spin up
        time.sleep(0.5)

    # Fake VISA address for demo
    target_visa = "USB0::0x1234::0x5678::INSTR"

    try:
        station = MySpecificTestStation(target_visa, target_port)
        station.run_test_sequence()
    finally:
        if 'emu' in locals():
            emu.stop()
