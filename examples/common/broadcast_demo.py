import time
import random
import os
import sys

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from instrumation.utils import DataBroadcaster

def main():
    """
    Broadcasting simulated peak power readings to 127.0.0.1:5005.
    """
    with DataBroadcaster(host="127.0.0.1", port=5005) as b:
        print("Broadcasting to 127.0.0.1:5005...")
        
        # If in simulation mode, only run for 5 iterations
        max_iters = 5 if os.environ.get("INSTRUMATION_MODE") == "SIM" else 100
        
        try:
            for i in range(max_iters):
                val = -45.0 + random.uniform(-2.0, 2.0)
                b.send({
                    "timestamp": time.time(),
                    "peak_power": round(val, 2),
                    "unit": "dBm"
                })
                print(f"Iteration {i+1}/{max_iters}")
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nBroadcasting stopped.")

if __name__ == "__main__":
    main()
