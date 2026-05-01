# VNA Complex Trace Capture

This example demonstrates how to capture complex I/Q data from a Vector Network Analyzer (VNA). This is used for measuring S-parameters (Magnitude and Phase).

## Code

```python
import numpy as np
from instrumation.factory import get_instrument

def run_vna_example(address="AUTO"):
    print(f"Connecting to VNA at {address}...")
    
    with get_instrument(address, "VNA") as vna:
        print(f"Connected to: {vna.get_id()}")
        
        # Configure sweep
        vna.set_start_frequency(1e9)
        vna.set_stop_frequency(2e9)
        vna.set_points(201)
        
        # Capture complex data (I/Q)
        result = vna.get_complex_trace("S21")
        
        # Capture the data as a numpy array for easy analysis
        complex_data = np.array(result.value)
        
        print(f"Captured {len(complex_data)} points.")
        print(f"First point: {complex_data[0]}")
        print(f"Magnitude at first point: {20 * np.log10(np.abs(complex_data[0])):.2f} dB")
        print(f"Phase at first point: {np.angle(complex_data[0], deg=True):.2f} deg")

if __name__ == "__main__":
    run_vna_example("AUTO")
```

## How it works

1.  **get_instrument**: Automatically detects the connected VNA or uses the Digital Twin if in `SIM` mode.
2.  **get_complex_trace**: Returns a `MeasurementResult` where `value` contains a list of complex numbers.
3.  **NumPy Integration**: We convert the list to a NumPy array to calculate Magnitude and Phase using standard math operations.
