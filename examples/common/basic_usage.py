import os
import sys
import time

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from instrumation.factory import get_instrument

def main():
    """
    Connects to a Digital Multimeter, sets it up for DC Voltage, and takes 5 readings.
    """
    # 1. Connect (Auto-discovery for first DMM found)
    with get_instrument("AUTO", "DMM") as dmm:
        
        print(f"Connected to: {dmm.get_id()}")
        
        # 2. Take multiple measurements
        for i in range(5):
            result = dmm.measure_voltage()
            print(f"Reading {i+1}: {result.value} {result.unit}")
            time.sleep(0.5)

    print("Done.")

if __name__ == "__main__":
    main()
