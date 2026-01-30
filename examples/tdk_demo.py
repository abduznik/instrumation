import os
import sys
import time

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Enable simulation mode for the demo, or comment out to try with real hardware if configured
os.environ["INSTRUMATION_MODE"] = "SIM" 

from instrumation.factory import get_instrument

def main():
    print("--- Starting TDK Power Supply Demo ---")
    
    # Check if we are in sim mode
    mode = os.environ.get("INSTRUMATION_MODE", "REAL")
    print(f"Mode: {mode}")

    try:
        # 1. Get the instrument
        # Replace with your actual VISA address, e.g., 'ASRL/dev/ttyUSB0::INSTR' or 'TCPIP::...'
        resource = "ASRL/dev/ttyUSB0::INSTR" 
        print(f"Connecting to {resource}...")
        
        psu = get_instrument(resource, "PSU")
        psu.connect()
        print(f"Instrument ID: {psu.get_id()}")

        # 2. Configure Output
        target_voltage = 5.0
        current_limit = 1.0
        
        print(f"\nSetting Voltage to {target_voltage}V and Current Limit to {current_limit}A...")
        psu.set_voltage(target_voltage)
        psu.set_current_limit(current_limit)
        
        # 3. Enable Output
        print("Enabling Output...")
        psu.set_output(True)
        time.sleep(1) # Wait for settle

        # 4. Measure
        meas_volt = psu.get_voltage()
        meas_curr = psu.get_current()
        
        print(f"Measured: {meas_volt:.3f} V, {meas_curr:.3f} A")
        
        # 5. Disable Output
        print("\nDisabling Output...")
        psu.set_output(False)
        
        psu.disconnect()
        print("\n--- Demo Complete ---")

    except Exception as e:
        print(f"Error: {e}")
        # import traceback
        # traceback.print_exc()

if __name__ == "__main__":
    main()
