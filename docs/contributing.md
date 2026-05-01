# Contributing

We welcome contributions to Instrumation!

## Development Setup
1. Clone the repository.
2. Install dependencies: `pip install -e .[test,docs]`
3. Run tests: `pytest`

## Adding New Drivers
1. Create a new file in `src/instrumation/drivers/`.
2. Inherit from the appropriate base class (e.g., `Multimeter`).
3. Use the `@register_driver("TYPE")` decorator.
4. Implement all abstract methods.
5. Add a simulated version to `simulated.py` for testing.
