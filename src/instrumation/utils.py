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
        return self

    def __exit__(self, *_):
        self.close()


class TestLogger:
    def __init__(self, filename="test_report.csv"):
        self.filename = filename
        if not os.path.exists(self.filename):
            self._write_header()

    def _write_header(self):
        with open(self.filename, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Test Name", "Data", "Result"])

    def log(self, test_name, data, result):
        with open(self.filename, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().isoformat(), test_name, data, result])
        print(f"Logged: {test_name} -> {result}")
