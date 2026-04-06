import time
import random
from instrumation.utils import DataBroadcaster

# Connect to the broadcaster on local port 5005
with DataBroadcaster(host="127.0.0.1", port=5005) as b:
    print("Broadcasting simulated peak power readings to 127.0.0.1:5005...")
    print("Press Ctrl+C to stop.")
    
    try:
        while True:
            # Simulate an instrument measurement
            val = -45.0 + random.uniform(-2.0, 2.0)
            
            # Send as JSON over UDP
            b.send({
                "timestamp": time.time(),
                "peak_power": round(val, 2),
                "unit": "dBm"
            })
            
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nBroadcasting stopped.")
