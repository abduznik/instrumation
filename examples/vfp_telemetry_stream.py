import time
import random
from instrumation.utils import DataBroadcaster
from instrumation.results import MeasurementResult

def stream_to_vfp():
    """
    Simulates a long-running test that streams live data to the Virtual Front Panel.
    """
    print("Starting VFP Telemetry Stream...")
    print("Make sure 'python -m instrumation.vfp_bridge' is running!")
    
    with DataBroadcaster() as broadcaster:
        for i in range(100):
            # Simulate a fluctuating measurement
            val = 24.0 + random.uniform(-0.5, 0.5)
            
            # Create a result with metadata for the dashboard
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
            
            # Send to bridge via UDP
            broadcaster.send(res.to_dict())
            
            if i % 10 == 0:
                print(f"Streamed {i} packets...")
                
            time.sleep(0.5)

if __name__ == "__main__":
    stream_to_vfp()
