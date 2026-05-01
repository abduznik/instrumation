import os
import sys
from instrumation.factory import get_instrument
from instrumation.exceptions import InstrumentTimeout, ConnectionLost, InstrumentError

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

def main():
    """
    Attempts to measure voltage with a robust retry mechanism using unified exceptions.
    """
    address = "AUTO"
    retries = 3
    attempt = 0
    
    while attempt < retries:
        try:
            print(f"Attempt {attempt + 1}: Connecting to DMM...")
            with get_instrument(address, "DMM") as dmm:
                res = dmm.measure_voltage()
                print(f"Measurement Success: {res.value} {res.unit}")
                return
        except InstrumentTimeout:
            print("Timeout occurred. Retrying...")
            attempt += 1
        except ConnectionLost:
            print("Connection lost. Check cables. Aborting.")
            break
        except InstrumentError as e:
            print(f"General instrument error: {e}. Retrying...")
            attempt += 1
    
    print("Failed to complete measurement.")

if __name__ == "__main__":
    main()
