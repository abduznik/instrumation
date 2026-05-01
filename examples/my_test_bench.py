import sys
import time
import os
from instrumation.factory import get_instrument
from instrumation import UUTHandler
from instrumation.exceptions import InstrumentError

def run_production_test():
    """
    A modern example of a production test sequence using the Instrumation HAL.
    """
    print("--- Starting Production Test Sequence ---")
    
    # 1. Connect to the Instrument (Using Factory)
    # This will use the Digital Twin (SIM) if the environment variable is set
    try:
        with get_instrument("AUTO", "DMM") as dmm:
            print(f"Connected to DMM: {dmm.get_id()}")
            
            # 2. Connect to the Unit Under Test (UUT)
            # For this demo, we'll use a try-except to handle cases where no serial hardware exists
            try:
                # In a real scenario, use a real port like 'COM3' or '/dev/ttyUSB0'
                # We'll use a dummy one for the demo
                with UUTHandler(serial_port="DUMMY_SERIAL", visa_address="DUMMY_VISA") as uut:
                    # 3. Test Step: Power On
                    print("Powering on UUT...")
                    # uut.send_command(b"POWER_ON")
                    time.sleep(0.5)
                    
                    # 4. Test Step: Measure Voltage
                    print("Measuring 5V Rail...")
                    res = dmm.measure_voltage()
                    print(f"Measured Voltage: {res}")
                    
                    # 5. Validation
                    if 4.75 <= res.value <= 5.25:
                        print("RESULT: PASS")
                    else:
                        print(f"RESULT: FAIL (Value {res.value} out of range)")
            except Exception as e:
                print(f"Serial/UUT connection skipped (No hardware). Measurement only: {dmm.measure_voltage()}")

    except InstrumentError as e:
        print(f"Hardware Error: {e}")
    except Exception as e:
        print(f"Unexpected Error: {e}")

if __name__ == "__main__":
    # Ensure simulation mode is on if no hardware is present
    if not os.environ.get("INSTRUMATION_MODE"):
        os.environ["INSTRUMATION_MODE"] = "SIM"
        
    run_production_test()
