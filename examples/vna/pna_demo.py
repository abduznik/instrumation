import os
import sys

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from instrumation.factory import get_instrument

def main():
    print("--- Starting PNA Demo ---")
    
    try:
        # 1. Get the instrument (Auto-discovery)
        with get_instrument("AUTO", "NA") as pna:
            print(f"Instrument ID: {pna.get_id()}")

            # 2. Configure measurement
            print("\nConfiguring Measurement...")
            pna.set_start_frequency(1e9) # 1 GHz
            pna.set_stop_frequency(5e9)  # 5 GHz
            pna.set_points(201)

            # 3. Get Data
            print("\nAcquiring Data...")
            res = pna.get_trace_data("S21")
            
            print(f"Received {len(res.value)} data points.")
            print(f"First 5 points: {res.value[:5]} {res.unit}")
            
        print("\n--- Demo Complete ---")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
