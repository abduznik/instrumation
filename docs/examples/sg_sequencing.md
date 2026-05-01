# Example: Signal Generator Sequencing

This example demonstrates how to use the new `SignalGenerator` class to create a frequency sweep.

## Goal
Generate a signal that steps from 1 GHz to 2 GHz in 100 MHz increments.

## The Script
```python
import time
from instrumation.factory import get_instrument

def frequency_sweep():
    # 1. Connect to the Keysight SG
    with get_instrument("TCPIP::192.168.1.50::INSTR", "SG") as sg:
        
        # 2. Setup initial state
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
    frequency_sweep()
```

## Why this is better
By using the standardized `SignalGenerator` interface, this same script will work with any supported signal generator (Keysight, Siglent, etc.) without changing a single line of code.
