import os
import sys

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from instrumation.factory import get_instrument

def main():
    """
    Demonstrates capturing a complex S21 trace from a VNA.
    """
    # Use AUTO discovery
    with get_instrument("AUTO", "VNA") as vna:
        print(f"Connected to: {vna.get_id()}")
        
        # Configure sweep
        vna.set_start_frequency(1.0e9)
        vna.set_stop_frequency(2.0e9)
        vna.set_points(401)
        
        print("Acquiring Complex S21 data...")
        result = vna.get_complex_trace("S21")
        
        # Access the numpy array of complex values
        trace = result.value
        print(f"Captured {len(trace)} complex points.")
        print("First 3 points (Real + j*Imag):")
        for val in trace[:3]:
            print(f"  {val}")

if __name__ == "__main__":
    main()
