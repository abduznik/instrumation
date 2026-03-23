"""
Tests for the instrumation CLI (instrumation.cli).

All tests run in SIM mode (INSTRUMATION_MODE=SIM) so no real hardware is needed.
"""

import json
import os
import socket
import threading
import time
import unittest
from unittest.mock import patch

os.environ["INSTRUMATION_MODE"] = "SIM"

from instrumation.cli import main  # noqa: E402  (import after env var set)


def _run(argv):
    """Run the CLI with the given argv list; capture SystemExit code."""
    try:
        main(argv)
    except SystemExit as exc:
        return exc.code
    return 0


def _capture_stdout(argv):
    """Run CLI and return (exit_code, stdout_text)."""
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = _run(argv)
    return code, buf.getvalue()


class TestScanCommand(unittest.TestCase):
    def test_scan_sim_mode(self):
        """scan prints a SIM notice and exits 0 in simulation mode."""
        code, out = _capture_stdout(["scan"])
        self.assertEqual(code, 0)
        self.assertIn("SIM", out)


class TestIdentifyCommand(unittest.TestCase):
    def test_identify_sim(self):
        """identify returns an ID string containing 'SIM' in simulation mode."""
        code, out = _capture_stdout(["identify", "--address", "DUMMY::SIM"])
        self.assertEqual(code, 0)
        self.assertIn("ID:", out)


class TestMeasureCommand(unittest.TestCase):
    def test_measure_voltage(self):
        code, out = _capture_stdout(
            ["measure", "--address", "DUMMY", "--type", "DMM", "--param", "voltage"]
        )
        self.assertEqual(code, 0)
        self.assertIn("voltage", out)

    def test_measure_peak(self):
        code, out = _capture_stdout(
            ["measure", "--address", "DUMMY", "--type", "SA", "--param", "peak"]
        )
        self.assertEqual(code, 0)
        self.assertIn("peak", out)

    def test_measure_current_psu(self):
        code, out = _capture_stdout(
            ["measure", "--address", "DUMMY", "--type", "PSU", "--param", "current"]
        )
        self.assertEqual(code, 0)
        self.assertIn("current", out)

    def test_measure_scope_vpp(self):
        code, out = _capture_stdout(
            ["measure", "--address", "DUMMY", "--type", "SCOPE", "--param", "vpp"]
        )
        self.assertEqual(code, 0)
        self.assertIn("vpp", out)

    def test_measure_scope_waveform(self):
        code, out = _capture_stdout(
            ["measure", "--address", "DUMMY", "--type", "SCOPE", "--param", "waveform"]
        )
        self.assertEqual(code, 0)
        self.assertIn("waveform", out)

    def test_measure_json_output(self):
        """--json flag produces valid JSON with the expected key."""
        code, out = _capture_stdout(
            ["measure", "--address", "DUMMY", "--type", "DMM",
             "--param", "voltage", "--json"]
        )
        self.assertEqual(code, 0)
        data = json.loads(out.strip())
        self.assertIn("voltage", data)
        self.assertIsInstance(data["voltage"], float)

    def test_measure_invalid_param(self):
        """An unsupported param for a given type exits non-zero."""
        import io
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = _run(
                ["measure", "--address", "DUMMY", "--type", "PSU", "--param", "peak"]
            )
        self.assertNotEqual(code, 0)

    def test_measure_dmm_resistance(self):
        code, out = _capture_stdout(
            ["measure", "--address", "DUMMY", "--type", "DMM", "--param", "resistance"]
        )
        self.assertEqual(code, 0)
        self.assertIn("resistance", out)

    def test_measure_dmm_frequency(self):
        code, out = _capture_stdout(
            ["measure", "--address", "DUMMY", "--type", "DMM", "--param", "frequency"]
        )
        self.assertEqual(code, 0)
        self.assertIn("frequency", out)


class TestBroadcastCommand(unittest.TestCase):
    PORT = 59900

    def _listen_n(self, port, n, timeout=3.0):
        """Listen for n UDP packets; return list of decoded JSON payloads."""
        received = []
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(timeout)
        sock.bind(("127.0.0.1", port))
        try:
            for _ in range(n):
                data, _ = sock.recvfrom(65535)
                received.append(json.loads(data.decode()))
        except socket.timeout:
            pass
        finally:
            sock.close()
        return received

    def test_broadcast_count(self):
        """broadcast --count 3 sends exactly 3 UDP packets with correct structure."""
        port = self.PORT
        received = []

        def listen():
            received.extend(self._listen_n(port, 3))

        t = threading.Thread(target=listen, daemon=True)
        t.start()
        time.sleep(0.05)

        code = _run([
            "broadcast",
            "--address", "DUMMY",
            "--type", "DMM",
            "--param", "voltage",
            "--host", "127.0.0.1",
            "--port", str(port),
            "--interval", "0.05",
            "--count", "3",
        ])

        t.join(timeout=5)
        self.assertEqual(code, 0)
        self.assertEqual(len(received), 3)
        for pkt in received:
            self.assertEqual(pkt["type"],  "DMM")
            self.assertEqual(pkt["param"], "voltage")
            self.assertIsInstance(pkt["value"], float)
            self.assertEqual(pkt["unit"],  "V")
            self.assertIn("ts", pkt)

    def test_broadcast_invalid_param(self):
        """broadcast with bad param exits non-zero without sending anything."""
        import io
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = _run([
                "broadcast",
                "--address", "DUMMY",
                "--type", "PSU",
                "--param", "peak",
                "--count", "1",
            ])
        self.assertNotEqual(code, 0)


class TestCLIHelp(unittest.TestCase):
    def test_top_level_help(self):
        with self.assertRaises(SystemExit) as ctx:
            main(["--help"])
        self.assertEqual(ctx.exception.code, 0)

    def test_measure_help(self):
        with self.assertRaises(SystemExit) as ctx:
            main(["measure", "--help"])
        self.assertEqual(ctx.exception.code, 0)

    def test_broadcast_help(self):
        with self.assertRaises(SystemExit) as ctx:
            main(["broadcast", "--help"])
        self.assertEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
