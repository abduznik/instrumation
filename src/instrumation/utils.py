"""Output helpers for streaming and recording test data.

Two independent utilities: :class:`DataBroadcaster` pushes readings onto the
network as UDP JSON for live dashboards, and :class:`TestLogger` appends
timestamped rows to a CSV report.

Both are built to never interrupt a running test -- errors are swallowed rather
than raised, which is convenient during a long measurement run and worth knowing
about when data appears to be missing.
"""

import csv
import json
import os
import socket
from datetime import datetime


class DataBroadcaster:
    """
    Broadcasts instrument data over UDP as JSON packets.

    Useful for streaming live readings to dashboards, loggers, or other
    listeners on the network with zero external dependencies.

    Parameters
    ----------
    host : str, optional
        Destination address. Defaults to ``"127.0.0.1"``.
    port : int, optional
        Destination UDP port. Defaults to ``5005``.

    Notes
    -----
    UDP is fire-and-forget: the socket is created eagerly and never verifies
    that anything is listening, so :meth:`send` succeeds whether or not a
    receiver exists.

    Usage::

        broadcaster = DataBroadcaster(host="127.0.0.1", port=5005)
        broadcaster.send({"voltage": 3.3, "current": 0.5})
        broadcaster.close()

    Or as a context manager::

        with DataBroadcaster() as b:
            b.send({"peak_power": -45.2})
    """

    def __init__(self, host="127.0.0.1", port=5005):
        self.host = host
        self.port = port
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, data):
        """
        Serialize *data* (dict or list) to JSON and send it as a UDP packet.
        Silently ignores transmission errors so the test flow is never interrupted.
        """
        try:
            payload = json.dumps(data).encode("utf-8")
            self._sock.sendto(payload, (self.host, self.port))
        except Exception:
            pass

    def close(self):
        """Close the underlying UDP socket."""
        try:
            self._sock.close()
        except Exception:
            pass

    def __enter__(self):
        """Return self, so the broadcaster can be used as a context manager."""
        return self

    def __exit__(self, *_):
        """Close the socket on context exit. Exceptions are not suppressed."""
        self.close()


class TestLogger:
    """Append-only CSV logger for test results.

    Writes one row per logged result with columns ``Timestamp``, ``Test Name``,
    ``Data`` and ``Result``. The header is written once, when the file is first
    created.

    Parameters
    ----------
    filename : str, optional
        Path to the CSV file. Defaults to ``"test_report.csv"`` in the working
        directory. An existing file is appended to, not overwritten, so results
        accumulate across runs.

    Notes
    -----
    Each :meth:`log` call opens the file, appends, and closes it. That keeps the
    report readable while a run is in progress -- and means a long run does many
    small writes rather than buffering.

    Examples
    --------
    >>> logger = TestLogger("run_2026-07-23.csv")
    >>> logger.log("output_power", -45.2, "PASS")
    """

    def __init__(self, filename="test_report.csv"):
        """Prepare the log file, writing a header if it does not yet exist.

        Parameters
        ----------
        filename : str, optional
            Path to the CSV file. Defaults to ``"test_report.csv"``.
        """
        self.filename = filename
        if not os.path.exists(self.filename):
            self._write_header()

    def _write_header(self):
        with open(self.filename, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Test Name", "Data", "Result"])

    def log(self, test_name, data, result):
        """Append one timestamped result row and echo it to stdout.

        Parameters
        ----------
        test_name : str
            Identifier for the measurement, used as the ``Test Name`` column.
        data : any
            The measured value. Written via ``csv``, so it is stringified --
            pass a pre-formatted string if you need a specific precision.
        result : any
            Pass/fail verdict or status, written to the ``Result`` column.

        Notes
        -----
        Also prints ``Logged: <test_name> -> <result>`` to stdout. Write errors
        are not caught here and will propagate, unlike elsewhere in this module.
        """
        with open(self.filename, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().isoformat(), test_name, data, result])
        print(f"Logged: {test_name} -> {result}")
