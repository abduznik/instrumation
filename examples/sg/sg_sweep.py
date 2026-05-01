import time
import os
import sys

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from instrumation.factory import get_instrument

def main():
    """
    Generate a signal that steps from 1 GHz to 2 GHz in 100 MHz increments.
    """
    # 1. Connect (Auto-discovery)
    with get_instrument("AUTO", "SG") as sg:
        
        # 2. Setup initial state
        print("Initializing Signal Generator...")
        sg.set_amplitude(-10.0)  # -10 dBm
        sg.set_output(True)
        
        # 3. Perform the sweep
        for freq in range(1000, 2100, 100):
            actual_freq = freq * 1e6  # Convert MHz to Hz
            print(f"Setting frequency to {freq} MHz...")
            sg.set_frequency(actual_freq)
            
            # Allow for settling time
            time.sleep(1.0)
            
        # 4. Cleanup
        sg.set_output(False)
        print("Sweep complete.")

if __name__ == "__main__":
    main()
