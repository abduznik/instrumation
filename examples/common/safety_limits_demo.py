"""
Example: Software Safety Guardrails (Anti-Gravity Guardrails)
"""
import os
import sys

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from instrumation import connect_instrument
from instrumation.exceptions import OverloadError, ConfigurationError

def main():
    print("--- Safety Guardrails Demo ---")
    
    # Connect to an SG (AUTO)
    with connect_instrument("AUTO", "SG") as sg:
        sg.max_power_dbm = 10.0
        sg.max_frequency = 6e9
        sg.min_frequency = 1e6
        
        print(f"Configured Limits: Power <= {sg.max_power_dbm} dBm, Freq [{sg.min_frequency}, {sg.max_frequency}] Hz")
        
        # 1. Test Power Limit
        print("\nAttempting to set power to +15 dBm (Unsafe)...")
        try:
            sg.set_amplitude(15.0)
        except OverloadError as e:
            print(f"CAUGHT: {e}")
            
        # 2. Test Frequency Limit
        print("\nAttempting to set frequency to 10 GHz (Unsafe)...")
        try:
            sg.set_frequency(10e9)
        except ConfigurationError as e:
            print(f"CAUGHT: {e}")
            
        # 3. Test Safe Command
        print("\nAttempting to set power to 0 dBm (Safe)...")
        sg.set_amplitude(0.0)
        print("Success!")

if __name__ == "__main__":
    main()
