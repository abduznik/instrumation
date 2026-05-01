# Log: MkDocs-Material Migration
**Commits**: `d5b9e9b`, `7185313`, `bc3bce3`

## Overview
Moved the entire documentation site from simple READMEs to a professional MkDocs-Material build. The goal was to make the HAL actually browsable and searchable.

## Technical Lowdown
- **Theme**: Switched to `material` theme with a clean, tech-focused color palette.
- **Auto-Docs**: Integrated `mkdocstrings` to automatically pull documentation from the Python source code.
- **CI/CD**: Added a GitHub Actions workflow to auto-deploy the site to GitHub Pages on every push to main.

## Why it matters
A library is only as good as its documentation. This migration gives us a professional landing page for users and makes it much easier to find specific driver methods and examples.
