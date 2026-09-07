import time
import random
import os
import sys

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from instrumation.utils import DataBroadcaster
from instrumation.results import MeasurementResult

# Each simulated instrument carries a stable "instrument_id" in its metadata
# so the dashboard can group incoming packets into one card per instrument
# instead of overwriting a single "last message" (see issue #119).
INSTRUMENTS = [
    {
        "instrument_id": "SA1@TCPIP::10.0.0.5::INSTR",
        "driver": "Siglent_SSA3000X",
        "unit": "dBm",
        "base": -45.0,
        "jitter": 0.5,
        "metadata_extra": {"frequency": 2400000000.0, "span": 1000000.0},
    },
    {
        "instrument_id": "DMM1@TCPIP::10.0.0.6::INSTR",
        "driver": "Keysight34461A",
        "unit": "V",
        "base": 5.0,
        "jitter": 0.02,
        "metadata_extra": {},
    },
]


def main():
    """
    Simulates a long-running test that streams live data from multiple
    instruments to the Virtual Front Panel.
    """
    print("Starting VFP Telemetry Stream...")

    with DataBroadcaster() as broadcaster:
        max_iters = 5 if os.environ.get("INSTRUMATION_MODE") == "SIM" else 100
        for i in range(max_iters):
            for inst in INSTRUMENTS:
                val = inst["base"] + random.uniform(-inst["jitter"], inst["jitter"])

                res = MeasurementResult(
                    value=round(val, 3),
                    unit=inst["unit"],
                    channel=1,
                    metadata={
                        "instrument_id": inst["instrument_id"],
                        "driver": inst["driver"],
                        **inst["metadata_extra"],
                    },
                )

                broadcaster.send(res.to_dict())

            if i % 10 == 0:
                print(f"Streamed {i} rounds...")

            time.sleep(0.5)

if __name__ == "__main__":
    main()
