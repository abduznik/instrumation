import json
import socket
import threading
import time
import unittest

from instrumation.utils import DataBroadcaster


def _listen_once(host, port, timeout=2.0):
    """Helper: bind a UDP socket, receive one packet, return decoded JSON."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(timeout)
    sock.bind((host, port))
    try:
        data, _ = sock.recvfrom(65535)
        return json.loads(data.decode("utf-8"))
    finally:
        sock.close()


class TestDataBroadcaster(unittest.TestCase):
    PORT = 59876  # high ephemeral port unlikely to conflict

    def test_send_dict(self):
        """DataBroadcaster sends a dict that a UDP listener can receive and decode."""
        result = {}

        def listen():
            result["payload"] = _listen_once("127.0.0.1", self.PORT)

        t = threading.Thread(target=listen, daemon=True)
        t.start()
        time.sleep(0.05)  # let listener bind before sending

        with DataBroadcaster(host="127.0.0.1", port=self.PORT) as b:
            b.send({"voltage": 3.3, "current": 0.5})

        t.join(timeout=3)
        self.assertEqual(result.get("payload"), {"voltage": 3.3, "current": 0.5})

    def test_send_list(self):
        """DataBroadcaster can send a list payload."""
        result = {}

        def listen():
            result["payload"] = _listen_once("127.0.0.1", self.PORT + 1)

        t = threading.Thread(target=listen, daemon=True)
        t.start()
        time.sleep(0.05)

        with DataBroadcaster(host="127.0.0.1", port=self.PORT + 1) as b:
            b.send([-45.2, -46.1, -44.8])

        t.join(timeout=3)
        self.assertEqual(result.get("payload"), [-45.2, -46.1, -44.8])

    def test_silent_on_error(self):
        """send() must not raise even when the socket is already closed."""
        b = DataBroadcaster(host="127.0.0.1", port=self.PORT + 2)
        b.close()
        # Should not raise
        b.send({"should": "not crash"})

    def test_context_manager(self):
        """DataBroadcaster works as a context manager and closes cleanly."""
        with DataBroadcaster(host="127.0.0.1", port=self.PORT + 3) as b:
            self.assertIsNotNone(b._sock)
        # After __exit__ the socket fd should be closed; sending must not raise
        b.send({"after": "close"})

    def test_multiple_sends(self):
        """Multiple send() calls on one broadcaster all arrive correctly."""
        received = []

        def listen():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(2.0)
            sock.bind(("127.0.0.1", self.PORT + 4))
            try:
                for _ in range(3):
                    data, _ = sock.recvfrom(65535)
                    received.append(json.loads(data.decode("utf-8")))
            except socket.timeout:
                pass
            finally:
                sock.close()

        t = threading.Thread(target=listen, daemon=True)
        t.start()
        time.sleep(0.05)

        with DataBroadcaster(host="127.0.0.1", port=self.PORT + 4) as b:
            b.send({"reading": 1})
            b.send({"reading": 2})
            b.send({"reading": 3})

        t.join(timeout=3)
        self.assertEqual(len(received), 3)
        self.assertEqual([r["reading"] for r in received], [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
