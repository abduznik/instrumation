import matplotlib.pyplot as plt
import pandas as pd
from instrumation.factory import get_instrument

def characterization_test():
    """
    Sweep a frequency range, capture power levels, save to CSV, and generate a plot.
    Matches docs/examples/plotting_and_data.md
    """
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
    # Set INSTRUMATION_MODE=SIM to run without hardware
    # Note: Requires 'pandas' and 'matplotlib' installed
    try:
        characterization_test()
    except ImportError:
        print("Error: This example requires 'pandas' and 'matplotlib' installed.")
