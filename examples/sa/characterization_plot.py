import matplotlib.pyplot as plt
import pandas as pd
import os
import sys

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from instrumation.factory import get_instrument

def main():
    """
    Sweep a frequency range, capture power levels, save to CSV, and generate a plot.
    """
    # 1. Connect (Auto-discovery)
    with get_instrument("AUTO", "SA") as sa:
        
        data = []
        frequencies = [1.0e9, 1.1e9, 1.2e9, 1.3e9, 1.4e9, 1.5e9]
        
        print(f"Testing {sa.get_id()}...")
        
        # 2. Collect Data
        for freq in frequencies:
            sa.set_center_freq(freq)
            sa.peak_search()
            res = sa.get_marker_amplitude()
            
            data.append({
                "Frequency_Hz": freq,
                "Power_dBm": res.value
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
    try:
        main()
    except ImportError:
        print("Error: This example requires 'pandas' and 'matplotlib' installed.")
    except Exception as e:
        print(f"An error occurred: {e}")
