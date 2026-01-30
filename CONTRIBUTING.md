# Contributing to Instrumation

Thank you for your interest in contributing to **Instrumation**! We welcome contributions from the community to help make this the best hardware abstraction layer for test benches.

## Local Development Setup

To set up your local development environment:

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/abduznik/instrumation.git
    cd instrumation
    ```

2.  **Install in editable mode**:
    This allows you to test your changes immediately without re-installing.
    ```bash
    pip install -e .
    ```

## Digital Twin Mode

You don't need physical hardware to contribute. You can run the library in **Digital Twin** mode, which simulates instruments with realistic physics/noise.

### 1. Enable Simulation Mode
Set the environment variable `INSTRUMATION_MODE` to `SIM`.

**Linux / Mac / Termux:**
```bash
export INSTRUMATION_MODE=SIM
```

**Windows (PowerShell):**
```powershell
$env:INSTRUMATION_MODE="SIM"
```

### 2. Run the Demo
Run the simulation example to verify everything is working:
```bash
python examples/sim_demo.py
```
You should see output indicating connection to `[SIM-PSU]`, `[SIM-DMM]`, etc.

## Running Tests
We use `pytest` for testing. Ensure you are in Simulation Mode before running tests (unless you have the specific hardware config).

```bash
# Ensure SIM mode is on
export INSTRUMATION_MODE=SIM 

# Run the test suite
pytest
```

## Adding a New Instrument Driver

Want to add support for a new device (e.g., Anritsu Spectrum Analyzer)? Follow these steps:

1.  **Inherit from Base**:
    Create a new file in `src/instrumation/drivers/` (e.g., `anritsu.py`).
    Import the abstract base class (e.g., `SpectrumAnalyzer` from `.base`) and implement the required methods (`peak_search`, `get_marker_amplitude`).

    ```python
    from .base import SpectrumAnalyzer

    class AnritsuMS2720T(SpectrumAnalyzer):
        def peak_search(self):
            self.inst.write("CALC:MARK1:MAX")
            
        def get_marker_amplitude(self) -> float:
            return float(self.inst.query("CALC:MARK1:Y?"))
    ```

2.  **Update the Factory**:
    Open `src/instrumation/factory.py`.
    Import your new class and add logic to return it based on the `driver_type`.

    ```python
    # Inside get_instrument or factory logic
    if driver_type == "SA":
        return AnritsuMS2720T(resource_address)
    ```

3.  **Submit a Pull Request**:
    Push your changes and open a PR. Our CI will automatically run the simulation tests.