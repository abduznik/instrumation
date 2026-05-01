import numpy as np
from instrumation.factory import get_instrument

def run_vna_example(address="AUTO"):
    """
    Demonstrates capturing a complex S21 trace from a VNA.
    """
    print(f"Connecting to VNA at {address}...")
    
    # Works with both "NA" and "VNA" aliases
    with get_instrument(address, "VNA") as vna:
        print(f"Connected to: {vna.get_id()}")
        
        # Configure sweep
        print("Configuring sweep: 1GHz to 2GHz, 201 points...")
        vna.set_start_frequency(1e9)
        vna.set_stop_frequency(2e9)
        vna.set_points(201)
        
        # Capture complex data (I/Q)
        print("Capturing S21 complex trace...")
        result = vna.get_complex_trace("S21")
        
        # result.value is a list/array of complex numbers
        complex_data = np.array(result.value)
        
        print(f"Captured {len(complex_data)} points.")
        print(f"First point: {complex_data[0]}")
        print(f"Magnitude at first point: {20 * np.log10(np.abs(complex_data[0])):.2f} dB")
        print(f"Phase at first point: {np.angle(complex_data[0], deg=True):.2f} deg")

if __name__ == "__main__":
    # Ensure INSTRUMATION_MODE=SIM if no hardware is connected
    run_vna_example("AUTO")
