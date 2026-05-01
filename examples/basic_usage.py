import time
from instrumation.factory import get_instrument

def run_basic_example():
    """
    Connects to a Digital Multimeter, sets it up for DC Voltage, and takes 5 readings.
    Matches docs/examples/basic_scripting.md
    """
    # 1. Connect (Auto-discovery for first DMM found)
    with get_instrument("AUTO", "DMM") as dmm:
        
        print(f"Connected to: {dmm.get_id()}")
        
        # 2. Take multiple measurements
        for i in range(5):
            result = dmm.measure_voltage()
            print(f"Reading {i+1}: {result.value} {result.unit}")
            time.sleep(0.5)

    # 3. Clean exit (handled by context manager)
    print("Done.")

if __name__ == "__main__":
    # Set INSTRUMATION_MODE=SIM to run without hardware
    run_basic_example()
