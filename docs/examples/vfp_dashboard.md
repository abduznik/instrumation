# VFP Live Telemetry Stream

This example shows how to stream live telemetry data from a test script to the Virtual Front Panel (VFP) dashboard.

## Code

```python
import time
import random
from instrumation.utils import DataBroadcaster
from instrumation.results import MeasurementResult

def stream_to_vfp():
    print("Starting VFP Telemetry Stream...")
    
    # Context manager automatically handles socket closing
    with DataBroadcaster() as broadcaster:
        for i in range(100):
            val = 24.0 + random.uniform(-0.5, 0.5)
            
            # Create a result with metadata for the dashboard cards
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
            time.sleep(0.5)

if __name__ == "__main__":
    stream_to_vfp()
```

## Running the dashboard

1.  Start the bridge: `python -m instrumation.vfp_bridge`
2.  Start the UI: `cd vfp-dashboard && npm run dev`
3.  Run this script.

The dashboard will automatically pick up the UDP packets from the bridge and update the charts and status cards in real-time.
