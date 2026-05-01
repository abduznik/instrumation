# Log: Squashing VNA Bugs
**Commit**: `b90b4e9`

## Overview
Quick patch to get the new VNA drivers actually working. They were missing some mandatory abstract methods which made them crash on startup.

## Technical Lowdown
- **Abstraction**: Implemented missing `write()`, `query()`, and `get_id()` requirements in the specific VNA driver classes.
- **Inheritance**: Fixed the MRO (Method Resolution Order) issues that were preventing the factory from correctly identifying the drivers.
- **Testing**: Added `tests/test_pna.py` to make sure these don't break again.

## Why it matters
The factory pattern only works if the drivers actually fulfill the contract defined in the base class. This fix ensured that `get_instrument("AUTO", "VNA")` actually returns a working object.
