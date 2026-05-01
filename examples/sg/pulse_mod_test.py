"""
Example: Pulse Modulation Control
Showcases standard set_mod_state() interface for radar/pulse testing.
"""
import os
import sys

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from instrumation import connect_instrument

def main():
    print("--- Pulse Modulation Demo ---")
    
    # Use AUTO discovery
    with connect_instrument("AUTO", "SG") as sg:
        sg.set_frequency(2.4e9)
        sg.set_amplitude(-10.0)
        
        print("Enabling Pulse Modulation...")
        sg.set_mod_state("PULSE", True)
        
        print("Toggling RF Output...")
        sg.set_output(True)
        
        print("Cleanup...")
        sg.shutdown_safety()

if __name__ == "__main__":
    main()
