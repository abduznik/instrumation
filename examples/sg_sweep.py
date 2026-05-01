import time
from instrumation.factory import get_instrument

def frequency_sweep():
    """
    Generate a signal that steps from 1 GHz to 2 GHz in 100 MHz increments.
    Matches docs/examples/sg_sequencing.md
    """
    # 1. Connect to the Signal Generator (using AUTO or a specific address)
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
    # Set INSTRUMATION_MODE=SIM to run without hardware
    frequency_sweep()
