"""
Example: Hardware List Sweep Demo
Showcases high-speed frequency/power steps using pre-loaded tables.
"""
import os
import sys
import time

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from instrumation import connect_instrument

def main():
    print("--- Hardware List Sweep Demo ---")
    
    with connect_instrument("AUTO", "SG") as sg:
        # Define sweep points (Hz, dBm)
        freqs = [1e9, 1.1e9, 1.2e9, 1.3e9, 1.4e9, 1.5e9]
        powers = [-20, -18, -16, -14, -12, -10]
        
        print(f"Loading {len(freqs)} points into hardware table...")
        sg.configure_list_sweep(freqs, powers)
        
        print("Starting continuous list sweep...")
        sg.start_sweep(1e9, 1.5e9, len(freqs), 0.1)
        
        time.sleep(2)
        print("Cleanup...")
        sg.shutdown_safety()

if __name__ == "__main__":
    main()
