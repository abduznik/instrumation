# Log: Modern Packaging (pyproject.toml)
**Commit**: `0b94054`

## Overview
Nuked the old `setup.py` and migrated the entire project to `pyproject.toml`. Keeping up with modern Python standards for dependency management and distribution.

## Technical Lowdown
- **Build System**: Switched to `setuptools` with a purely declarative configuration in `pyproject.toml`.
- **Dependencies**: Consolidated all project metadata and requirements into a single, standard file.
- **Cleanup**: Removed legacy build artifacts and simplified the installation process for both users and developers.

## Why it matters
`setup.py` is increasingly deprecated in the Python ecosystem. Moving to `pyproject.toml` makes the project more maintainable, easier to publish to PyPI, and compatible with modern tools like Poetry, PDM, and uv.
