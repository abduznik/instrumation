# Example: Plotting and Data Analysis

This example demonstrates the "Frictionless" nature of Instrumation. You can develop your entire analysis pipeline (using `matplotlib` and `pandas`) in Simulation mode and then swap to real hardware with zero code changes.

## Goal
Sweep a frequency range, capture power levels, save the data to a CSV file, and generate a plot.

## The Script
```python
import matplotlib.pyplot as plt
import pandas as pd
from instrumation.factory import get_instrument

def characterization_test():
    # 1. Connect (Works in SIM or REAL mode)
    with get_instrument("AUTO", "SA") as sa:
        
        data = []
        frequencies = [1.0e9, 1.1e9, 1.2e9, 1.3e9, 1.4e9, 1.5e9]
        
        print(f"Testing {sa.get_id()}...")
        
        # 2. Collect Data
        for freq in frequencies:
            # sa.set_center_frequency(freq)
            res = sa.get_peak_value()
            
            data.append({
                "Frequency_Hz": freq,
                "Power_dBm": res.value,
                "Status": res.status
            })
            
        # 3. Process with Pandas
        df = pd.DataFrame(data)
        df.to_csv("test_results.csv", index=False)
        print("Data saved to test_results.csv")
        
        # 4. Plot with Matplotlib
        plt.figure(figsize=(10, 5))
        plt.plot(df["Frequency_Hz"] / 1e9, df["Power_dBm"], marker='o', linestyle='-')
        plt.title(f"Device Characterization - {sa.get_id()}")
        plt.xlabel("Frequency (GHz)")
        plt.ylabel("Power (dBm)")
        plt.grid(True)
        plt.savefig("characterization_plot.png")
        print("Plot saved to characterization_plot.png")

if __name__ == "__main__":
    characterization_test()
```

## Why it is "Frictionless"
- **Unified Results**: Both the `SimulatedSpectrumAnalyzer` and the real `KeysightSA` return the exact same `MeasurementResult` object.
- **Environment Driven**: By just changing `export INSTRUMATION_MODE=SIM`, you can run this script on your laptop without any hardware. When you plug in the instrument, unset the variable, and the script "just works".
- **Deterministic Simulation**: In simulation mode, the results follow a predictable pattern (or random noise), allowing you to verify that your `pandas` logic and `matplotlib` styling are correct before you ever step into the lab.
