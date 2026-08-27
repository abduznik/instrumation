"""Configuration helpers.

:func:`get_config` returns the configuration dictionary used by the test
station. Values are resolved with this precedence (highest wins):
environment variables > config file > built-in defaults.
"""

import json
import os
from pathlib import Path


def is_sim_mode() -> bool:
    """
    Checks the INSTRUMATION_MODE environment variable.
    Returns True if set to 'SIM', else False.
    """
    mode = os.environ.get("INSTRUMATION_MODE", "").upper()
    return mode == "SIM" or mode == "SIMULATED"


_DEFAULTS = {
    "visa_address": "USB0::0x2A8D::0x1301::MY54400000::0::INSTR",
    "serial_port": "COM3",
    "instrument_type": "DMM",
    "log_file": "test_report.csv",
}

_ENV_MAP = {
    "visa_address": "VISA_ADDRESS",
    "serial_port": "SERIAL_PORT",
    "instrument_type": "INSTRUMENT_TYPE",
    "log_file": "LOG_FILE",
}

_FILE_NAMES = ("instrumation.json", "instrumation.yaml", "instrumation.yml")


def _default_config() -> dict:
    """Built-in defaults (env vars are applied later, with higher precedence)."""
    return dict(_DEFAULTS)


def _find_config_file() -> Path | None:
    """Locate a JSON/YAML config file if one exists.

    Resolution order:
      1. ``INSTRUMATION_CONFIG`` env var pointing at an explicit path
      2. ``instrumation.json`` / ``instrumation.yaml`` / ``instrumation.yml``
         in the current working directory
      3. Same filenames in the user's home directory
    """
    explicit = os.environ.get("INSTRUMATION_CONFIG")
    if explicit:
        p = Path(explicit).expanduser()
        return p if p.is_file() else None

    for name in _FILE_NAMES:
        for base in (Path.cwd(), Path.home()):
            candidate = base / name
            if candidate.is_file():
                return candidate
    return None


def _load_config_file(path: Path) -> dict:
    """Load a JSON or YAML config file into a dict. YAML needs PyYAML; JSON is
    stdlib-only."""
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        try:
            import yaml  # optional dependency

            loaded = yaml.safe_load(text) or {}
        except ImportError:
            raise RuntimeError(
                f"YAML config file found but PyYAML is not installed: {path}"
            )
    else:
        loaded = json.loads(text)
    if not isinstance(loaded, dict):
        raise ValueError(f"Config file {path} must contain a JSON/YAML object")
    return loaded


def get_config() -> dict:
    """
    Returns the configuration dictionary for the test station.

    Resolution precedence (highest wins):
        1. Environment variables (``VISA_ADDRESS``, ``SERIAL_PORT``,
           ``INSTRUMENT_TYPE``, ``LOG_FILE``)
        2. A config file, located via the ``INSTRUMATION_CONFIG`` env var or
           ``instrumation.{json,yaml,yml}`` in the current directory or the
           user's home directory
        3. Built-in defaults

    Example::

        config = get_config()
        visa = config["visa_address"]
    """
    cfg = _default_config()

    config_file = _find_config_file()
    if config_file is not None:
        cfg.update(_load_config_file(config_file))

    # Environment variables always win over defaults and the file.
    for key, env_name in _ENV_MAP.items():
        if os.environ.get(env_name):
            cfg[key] = os.environ[env_name]
    return cfg