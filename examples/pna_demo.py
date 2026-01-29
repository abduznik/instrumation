import os
import sys

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Enable simulation mode
os.environ["INSTRUMATION_MODE"] = "SIM"

from instrumation.factory import get_instrument

def main():
    print("--- Starting PNA Demo (Simulation) ---")
    
    try:
        # 1. Get the instrument
        pna = get_instrument("TCPIP0::192.168.1.100::inst0::INSTR", "NA")
        pna.connect()
        print(f"Instrument ID: {pna.get_id()}")

        # 2. Configure measurement
        print("\nConfiguring Measurement...")
        pna.set_start_frequency(1e9) # 1 GHz
        pna.set_stop_frequency(5e9)  # 5 GHz
        pna.set_points(201)

        # 3. Get Data
        print("\nAcquiring Data...")
        # Simulate getting S21
        data = pna.get_trace_data("S21")
        
        print(f"Received {len(data)} data points.")
        print(f"First 5 points: {data[:5]}")
        
        pna.disconnect()
        print("\n--- Demo Complete ---")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

