import matplotlib.pyplot as plt
from instrumation.factory import get_instrument

def generate_report():
    """
    Demonstrates using the replay:// protocol to perform offline analysis.
    Matches docs/examples/recording_to_plot.md
    """
    # Use the replay protocol - no hardware needed!
    # To run this, you first need a recording file.
    # instrumation record "ADDRESS" DMM lab_data.json
    address = "replay://lab_data.json"
    
    try:
        with get_instrument(address, "DMM") as dmm:
            results = []
            
            # This will pull the exact values you recorded
            print(f"Replaying data from: {address}")
            for _ in range(10):
                res = dmm.measure_voltage()
                results.append(res.value)
                
            # Generate the visualization
            plt.plot(results, 'r-x')
            plt.title("Post-Lab Analysis (Replay Mode)")
            plt.ylabel("Voltage (V)")
            plt.savefig("lab_report.png")
            print("Report generated successfully from recorded data.")
            
    except FileNotFoundError:
        print("Error: lab_data.json not found. Run the recording command first.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    generate_report()
