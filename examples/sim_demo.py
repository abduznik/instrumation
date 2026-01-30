import os
import sys
import time

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Enable Simulation Mode
os.environ["INSTRUMATION_MODE"] = "SIM"

from instrumation.factory import get_instrument

def run_simulation_demo():
    print("--- Digital Twin Test Bench Simulation ---\n")
    
    # 1. Power Supply
    print("1. Initializing Power Supply...")
    psu = get_instrument("GPIB::1", "PSU")
    psu.connect()
    print(f"   ID: {psu.get_id()}")
    
    target_v = 12.0
    print(f"   Setting Voltage to {target_v}V...")
    psu.set_voltage(target_v)
    psu.set_output(True)
    
    curr = psu.get_current()
    print(f"   Measured Current Draw: {curr:.3f} A")
    psu.disconnect()
    print("")

    # 2. Multimeter
    print("2. Initializing Multimeter...")
    dmm = get_instrument("USB::2", "DMM")
    dmm.connect()
    print(f"   ID: {dmm.get_id()}")
    
    res = dmm.measure_resistance()
    print(f"   Resistor Measurement: {res:.2f} Ohms")
    dmm.disconnect()
    print("")

    # 3. Spectrum Analyzer
    print("3. Initializing Spectrum Analyzer...")
    sa = get_instrument("LAN::3", "SA")
    sa.connect()
    print(f"   ID: {sa.get_id()}")
    
    print("   Performing Peak Search...")
    peak_val = sa.get_peak_value()
    print(f"   Peak Amplitude Found: {peak_val:.2f} dBm")
    sa.disconnect()
    
    print("\n--- Simulation Complete ---")

if __name__ == "__main__":
    run_simulation_demo()