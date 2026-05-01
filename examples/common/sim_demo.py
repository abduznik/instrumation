import os
import sys
import time

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from instrumation.factory import get_instrument

def main():
    print("--- Digital Twin Test Bench Simulation ---\n")
    
    # 1. Power Supply
    print("1. Initializing Power Supply (AUTO)...")
    with get_instrument("AUTO", "PSU") as psu:
        print(f"   ID: {psu.get_id()}")
        
        target_v = 12.0
        print(f"   Setting Voltage to {target_v}V...")
        psu.set_voltage(target_v)
        psu.set_output(True)
        
        curr = psu.get_current()
        print(f"   Measured Current Draw: {curr.value:.3f} {curr.unit}")
    print("")

    # 2. Multimeter
    print("2. Initializing Multimeter (AUTO)...")
    with get_instrument("AUTO", "DMM") as dmm:
        print(f"   ID: {dmm.get_id()}")
        
        res = dmm.measure_resistance()
        print(f"   Resistor Measurement: {res.value:.2f} {res.unit}")
    print("")

    # 3. Spectrum Analyzer
    print("3. Initializing Spectrum Analyzer (AUTO)...")
    with get_instrument("AUTO", "SA") as sa:
        print(f"   ID: {sa.get_id()}")
        
        print("   Performing Peak Search...")
        sa.peak_search()
        peak_amp = sa.get_marker_amplitude()
        print(f"   Peak Amplitude Found: {peak_amp.value:.2f} {peak_amp.unit}")
    
    print("\n--- Simulation Complete ---")

if __name__ == "__main__":
    main()