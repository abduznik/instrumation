# Contributing to Instrumation

Thank you for your interest in contributing to **Instrumation**! We welcome contributions from the community to help make this the best hardware abstraction layer for test benches.

## Local Development Setup

To set up your local development environment:

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/abduznik/instrumation.git
    cd instrumation
    ```

2.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Linux / Mac
    # .venv\Scripts\activate   # Windows (PowerShell)
    ```

3.  **Install in editable mode with test and docs extras**:
    This allows you to test your changes immediately without re-installing.
    ```bash
    pip install -e ".[test,docs]"
    ```

    Available extras:
    - `test` — pytest and pytest-asyncio for running the test suite
    - `docs` — mkdocs-material and mkdocstrings for building documentation
    - No extra needed for core dependencies (pyvisa, pyserial, toml, numpy, websockets)

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

# Run the full test suite
pytest

# Run a specific test file
pytest tests/test_psu.py

# Run tests matching a keyword
pytest -k "simulation"

# Run with verbose output
pytest -v
```

## Code Style

This project uses **flake8** for linting with the following configuration:

- **Line length limit**: 127 characters
- **Max complexity**: 10 (cyclomatic complexity)
- The CI checks for Python syntax errors and undefined names as hard failures (`E9`, `F63`, `F7`, `F82`)

To check your code locally before pushing:

```bash
# Check for syntax errors and undefined names (will fail CI if violated)
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Full lint check (warnings, not blocking)
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

## Pre-commit Checklist

Before opening a pull request, verify the following:

1. **Lint passes** — Run the flake8 checks above and fix any errors
2. **Tests pass** — Run `pytest` in SIM mode and ensure all tests pass
3. **No unrelated changes** — Keep your diff focused on the issue you're addressing
4. **Commit messages** — Use clear, descriptive commit messages (see PR Workflow below)

## PR Workflow

### Branch Naming

Use descriptive branch names with a type prefix:

- `feat/short-description` — new features or instrument drivers
- `fix/short-description` — bug fixes
- `docs/short-description` — documentation changes
- `refactor/short-description` — code restructuring without behavior changes
- `test/short-description` — adding or updating tests

### Commit Style

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): short description

Optional longer explanation of what changed and why.
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

Examples:
```
feat(drivers): add Anritsu MS2720T spectrum analyzer driver
fix(psu): correct voltage readback rounding error
docs(readme): update installation instructions
```

### Linking Issues

Reference the issue your PR addresses in the commit message or PR description:

```
Closes #42
```

This automatically closes the issue when the PR is merged.

### Opening the PR

1. Push your branch to your fork
2. Open a PR against the `main` branch
3. Fill in the PR description with:
   - What changed and why
   - How to test the change
   - Reference to the related issue

## Issue Labels

| Label | Meaning |
|-------|---------|
| `good first issue` | Suitable for newcomers; well-scoped and documented |
| `help wanted` | Maintainers would appreciate community help |
| `bug` | Something isn't working as expected |
| `enhancement` | New feature or improvement |
| `documentation` | Documentation improvements |
| `drivers` | Related to instrument driver implementations |

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

3.  **Add Tests**:
    Create a test file in `tests/` (e.g., `test_anritsu.py`) that verifies your driver works in simulation mode.

4.  **Submit a Pull Request**:
    Push your changes and open a PR. Our CI will automatically run the simulation tests.
