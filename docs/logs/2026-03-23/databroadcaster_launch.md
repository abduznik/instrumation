# Log: DataBroadcaster Launch
**Commit**: `a4961ce`

## Overview
The birth of the `DataBroadcaster`. We implemented a high-performance UDP streaming engine to allow instruments to broadcast their data live to any listener on the network.

## Technical Lowdown
- **UDP Streaming**: Implemented a non-blocking UDP sender that can broadcast JSON-serialized measurement data.
- **Async Support**: Designed the broadcaster to be fully compatible with our async measurement loop.
- **Extensibility**: Laid the groundwork for the `VFPBridge` and web-based dashboards by using a standard JSON-over-UDP protocol.

## Why it matters
This transformed the HAL from a "query-response" library into a live telemetry system. It's what allows us to have live dashboards and real-time visualization of high-speed measurements without blocking the main control loop.
