import sys
import time
import os

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from instrumation.factory import get_instrument
from instrumation import UUTHandler
from instrumation.exceptions import InstrumentError

def main():
    """
    A modern example of a production test sequence using the Instrumation HAL.
    """
    print("--- Starting Production Test Sequence ---")
    
    try:
        with get_instrument("AUTO", "DMM") as dmm:
            print(f"Connected to DMM: {dmm.get_id()}")
            
            try:
                # Use a dummy port for demonstration
                with UUTHandler(serial_port="DUMMY_SERIAL", visa_address="DUMMY_VISA"):
                    print("Powering on UUT...")
                    time.sleep(0.5)
                    
                    print("Measuring 5V Rail...")
                    res = dmm.measure_voltage()
                    print(f"Measured Voltage: {res.value} {res.unit}")
                    
                    if 4.75 <= res.value <= 5.25:
                        print("RESULT: PASS")
                    else:
                        print(f"RESULT: FAIL (Value {res.value} out of range)")
            except Exception:
                print(f"UUT connection skipped (No hardware). Measurement only: {dmm.measure_voltage()}")

    except InstrumentError as e:
        print(f"Hardware Error: {e}")
    except Exception as e:
        print(f"Unexpected Error: {e}")

if __name__ == "__main__":
    main()
