import os
import sys
import matplotlib.pyplot as plt

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from instrumation.factory import get_instrument

def main():
    """
    Demonstrates using the replay:// protocol to perform offline analysis.
    """
    # Look for the data file in the same directory as this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(current_dir, "lab_data.json")
    address = f"replay://{data_file}"
    
    try:
        with get_instrument(address, "DMM") as dmm:
            results = []
            
            print(f"Replaying data from: {data_file}")
            for _ in range(10):
                res = dmm.measure_voltage()
                results.append(res.value)
                
            plt.plot(results, 'r-x')
            plt.title("Post-Lab Analysis (Replay Mode)")
            plt.ylabel("Voltage (V)")
            plt.savefig("lab_report.png")
            print("Report generated successfully from recorded data.")
            
    except FileNotFoundError:
        print(f"Error: {data_file} not found. Run the recording command first.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
