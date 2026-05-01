import time
import random
import os
import sys

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from instrumation.utils import DataBroadcaster
from instrumation.results import MeasurementResult

def main():
    """
    Simulates a long-running test that streams live data to the Virtual Front Panel.
    """
    print("Starting VFP Telemetry Stream...")
    
    with DataBroadcaster() as broadcaster:
        max_iters = 5 if os.environ.get("INSTRUMATION_MODE") == "SIM" else 100
        for i in range(max_iters):
            # Simulate a fluctuating measurement
            val = 24.0 + random.uniform(-0.5, 0.5)
            
            res = MeasurementResult(
                value=round(val, 3),
                unit="dBm",
                channel=1,
                metadata={
                    "driver": "Siglent_SSA3000X",
                    "frequency": 2400000000.0,
                    "span": 1000000.0
                }
            )
            
            broadcaster.send(res.to_dict())
            
            if i % 10 == 0:
                print(f"Streamed {i} packets...")
                
            time.sleep(0.5)

if __name__ == "__main__":
    main()
