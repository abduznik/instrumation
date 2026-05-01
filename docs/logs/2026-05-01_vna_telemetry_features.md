# Log: VNAs & Telemetry (New Features)
**Commits**: `e068a1e`, `fa6d67c`, `f154ee8`

## Overview
A massive push to add high-end instrument support and better telemetry tools. We also spent some time making sure the documentation actually matches the code.

## Technical Lowdown
- **VNA Support**: Added full support for Vector Network Analyzers. You can now use `VNA` or `NA` aliases in the factory.
- **VFP Bridge**: Implemented a bridge that relays UDP telemetry packets to WebSockets for live dashboarding.
- **Complex Data**: Added `get_complex_trace()` for S-parameter measurements (Real + Imaginary support).
- **Docs Sync**: Scrubbed the `docs/` folder to ensure every code snippet in the markdown files actually works with the new standalone examples.

## Why it matters
The HAL is moving beyond basic DMMs and PSUs. Adding VNA support and live telemetry makes it a serious tool for RF engineering and long-term characterization tests.
