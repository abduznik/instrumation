# Example: Recording to Plot (Offline Analysis)

This workflow shows how to "bring the lab home with you". You can record a complex measurement sequence in the lab and then use that exact data to iterate on your visualization scripts offline.

## Step 1: Record in the Lab
Use the CLI to capture a real session from your instrument.

```bash
instrumation record "GPIB0::7::INSTR" DMM lab_data.json
```
*Manual queries like `MEAS:VOLT:DC?` are performed here.*

## Step 2: Plot at Home
Back at your desk, use the `replay://` protocol to feed that exact data into your plotting script.

```python
import matplotlib.pyplot as plt
from instrumation.factory import get_instrument

def generate_report():
    # Use the replay protocol - no hardware needed!
    address = "replay://lab_data.json"
    
    with get_instrument(address, "DMM") as dmm:
        results = []
        
        # This will pull the exact values you recorded in Step 1
        for _ in range(10):
            res = dmm.measure_voltage()
            results.append(res.value)
            
        # Generate the visualization
        plt.plot(results, 'r-x')
        plt.title("Post-Lab Analysis (Replay Mode)")
        plt.ylabel("Voltage (V)")
        plt.savefig("lab_report.png")
        print("Report generated successfully from recorded data.")

if __name__ == "__main__":
    generate_report()
```

## Why this is powerful
- **No Data Loss**: You don't just save a single value; you save the entire "interaction" with the instrument.
- **Deterministic**: Every time you run the script at home, it will produce the exact same plot, making it perfect for fine-tuning your visualization code.
- **Shared Debugging**: You can send the `lab_data.json` file to a colleague, and they can run your script and see exactly what you saw in the lab.
