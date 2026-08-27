"""Issue #165: get_config() was a stub that never loaded JSON/YAML.

Covers: defaults, env-var overrides, JSON file loading, env-over-file
precedence, INSTRUMATION_CONFIG explicit path, and extra keys from file.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path

from instrumation.config import get_config


class TestGetConfig(unittest.TestCase):
    def setUp(self):
        self._saved = {
            k: os.environ.get(k)
            for k in ("INSTRUMATION_CONFIG", "VISA_ADDRESS", "SERIAL_PORT",
                      "INSTRUMENT_TYPE", "LOG_FILE")
        }
        for k in self._saved:
            os.environ.pop(k, None)
        self._old_cwd = Path.cwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)

    def tearDown(self):
        os.chdir(self._old_cwd)
        self._tmp.cleanup()
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_defaults_without_env_or_file(self):
        cfg = get_config()
        self.assertEqual(cfg["visa_address"], "USB0::0x2A8D::0x1301::MY54400000::0::INSTR")
        self.assertEqual(cfg["serial_port"], "COM3")
        self.assertEqual(cfg["instrument_type"], "DMM")
        self.assertEqual(cfg["log_file"], "test_report.csv")

    def test_env_vars_override_defaults(self):
        os.environ["VISA_ADDRESS"] = "TCPIP0::10.0.0.5::INSTR"
        os.environ["SERIAL_PORT"] = "COM7"
        os.environ["INSTRUMENT_TYPE"] = "SA"
        cfg = get_config()
        self.assertEqual(cfg["visa_address"], "TCPIP0::10.0.0.5::INSTR")
        self.assertEqual(cfg["serial_port"], "COM7")
        self.assertEqual(cfg["instrument_type"], "SA")

    def test_json_file_in_cwd(self):
        (Path.cwd() / "instrumation.json").write_text(
            json.dumps({"visa_address": "GPIB0::12::INSTR", "log_file": "run.json.csv"}),
            encoding="utf-8",
        )
        cfg = get_config()
        self.assertEqual(cfg["visa_address"], "GPIB0::12::INSTR")
        self.assertEqual(cfg["log_file"], "run.json.csv")
        self.assertEqual(cfg["serial_port"], "COM3")  # defaults fill the gaps

    def test_env_overrides_file(self):
        (Path.cwd() / "instrumation.json").write_text(
            json.dumps({"visa_address": "GPIB0::12::INSTR"}),
            encoding="utf-8",
        )
        os.environ["VISA_ADDRESS"] = "USB0::0x9999::INSTR"
        cfg = get_config()
        self.assertEqual(cfg["visa_address"], "USB0::0x9999::INSTR")

    def test_instrumation_config_explicit_path(self):
        config_dir = Path(self._tmp.name) / "etc"
        config_dir.mkdir()
        config_path = config_dir / "custom.json"
        config_path.write_text(
            json.dumps({"visa_address": "ASRL5::INSTR", "instrument_type": "PSU"}),
            encoding="utf-8",
        )
        os.environ["INSTRUMATION_CONFIG"] = str(config_path)
        cfg = get_config()
        self.assertEqual(cfg["visa_address"], "ASRL5::INSTR")
        self.assertEqual(cfg["instrument_type"], "PSU")

    def test_extra_keys_from_file_are_kept(self):
        (Path.cwd() / "instrumation.json").write_text(
            json.dumps({"timeout_sec": 30}),
            encoding="utf-8",
        )
        cfg = get_config()
        self.assertEqual(cfg.get("timeout_sec"), 30)

    def test_missing_explicit_path_falls_back_to_defaults(self):
        os.environ["INSTRUMATION_CONFIG"] = str(Path.cwd() / "does-not-exist.json")
        cfg = get_config()
        self.assertEqual(cfg["visa_address"], "USB0::0x2A8D::0x1301::MY54400000::0::INSTR")

    def test_bad_json_file_raises(self):
        (Path.cwd() / "instrumation.json").write_text("{not json", encoding="utf-8")
        with self.assertRaises(ValueError):
            get_config()

    def test_non_object_json_raises(self):
        (Path.cwd() / "instrumation.json").write_text("[1, 2, 3]", encoding="utf-8")
        with self.assertRaises(ValueError):
            get_config()


if __name__ == "__main__":
    unittest.main()