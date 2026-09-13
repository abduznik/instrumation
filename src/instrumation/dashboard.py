"""Single-call launcher for the Virtual Front Panel dashboard.

Ties together the three VFP components -- the UDP/WebSocket bridge
(:class:`~instrumation.vfp_bridge.VFPBridge`), a static file server for the
built React app, and a small REST API for exporting current readings -- so a
script can start the whole dashboard with one call instead of running the
bridge and ``npm run dev`` by hand.

Usage::

    from instrumation.dashboard import launch_dashboard

    handle = launch_dashboard()
    # ... run your test session, streaming via DataBroadcaster ...
    handle.stop()
"""

import asyncio
import csv
import io
import json
import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from .vfp_bridge import VFPBridge

logger = logging.getLogger(__name__)

DEFAULT_HTTP_PORT = 8080
DEFAULT_WS_PORT = 8765
DEFAULT_UDP_PORT = 9999

DEFAULT_DIST_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "vfp-dashboard",
    "dist",
)


def _readings_to_rows(readings):
    """Flattens the bridge's latest-readings map into one row per reading."""
    rows = []
    for instrument_id, payload in readings.items():
        metadata = payload.get("metadata") or {}
        rows.append(
            {
                "instrument": instrument_id,
                "parameter": metadata.get("parameter", ""),
                "value": payload.get("value", ""),
                "unit": payload.get("unit", ""),
                "timestamp": payload.get("timestamp", ""),
            }
        )
    return rows


def _make_request_handler(bridge: VFPBridge, dist_dir: str):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            logger.debug("%s - %s", self.address_string(), fmt % args)

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == "/api/readings":
                self._handle_readings(parse_qs(parsed.query))
            else:
                self._handle_static(parsed.path)

        def _handle_readings(self, query):
            rows = _readings_to_rows(bridge.latest_readings)
            fmt = query.get("format", ["json"])[0].lower()

            if fmt == "csv":
                buf = io.StringIO()
                writer = csv.DictWriter(
                    buf, fieldnames=["instrument", "parameter", "value", "unit", "timestamp"]
                )
                writer.writeheader()
                writer.writerows(rows)
                body = buf.getvalue().encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/csv")
                self.send_header("Content-Disposition", 'attachment; filename="readings.csv"')
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                body = json.dumps(rows).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        def _handle_static(self, path):
            if path == "/":
                path = "/index.html"
            safe_rel = os.path.normpath(path).lstrip(os.sep)
            file_path = os.path.join(dist_dir, safe_rel)

            if not os.path.abspath(file_path).startswith(os.path.abspath(dist_dir)):
                self.send_error(403)
                return

            if not os.path.isfile(file_path):
                file_path = os.path.join(dist_dir, "index.html")

            if not os.path.isfile(file_path):
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(
                    b"VFP dashboard build not found. Run `npm run build` in vfp-dashboard/."
                )
                return

            content_type = "text/html"
            if file_path.endswith(".js"):
                content_type = "application/javascript"
            elif file_path.endswith(".css"):
                content_type = "text/css"
            elif file_path.endswith(".json"):
                content_type = "application/json"
            elif file_path.endswith(".svg"):
                content_type = "image/svg+xml"
            elif file_path.endswith(".png"):
                content_type = "image/png"

            with open(file_path, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


class DashboardHandle:
    """Handles to the three running servers, returned by :func:`launch_dashboard`."""

    def __init__(self, bridge: VFPBridge, http_server: ThreadingHTTPServer, loop, bridge_thread, http_thread):
        self.bridge = bridge
        self.http_server = http_server
        self._loop = loop
        self._bridge_thread = bridge_thread
        self._http_thread = http_thread

    def stop(self, timeout: float = 5.0) -> None:
        """Shuts down the HTTP server and the asyncio bridge loop cleanly."""
        self.http_server.shutdown()
        self.http_server.server_close()
        self._http_thread.join(timeout=timeout)

        def cancel_tasks():
            for task in asyncio.all_tasks(loop=self._loop):
                task.cancel()

        self._loop.call_soon_threadsafe(cancel_tasks)
        self._bridge_thread.join(timeout=timeout)


def launch_dashboard(
    http_port: int = DEFAULT_HTTP_PORT,
    ws_port: int = DEFAULT_WS_PORT,
    udp_port: int = DEFAULT_UDP_PORT,
    host: str = "127.0.0.1",
    dist_dir: str = DEFAULT_DIST_DIR,
) -> DashboardHandle:
    """Starts the VFP bridge, static file server, and REST API in one call.

    Parameters
    ----------
    http_port : int, optional
        Port to serve the built dashboard and ``/api/readings`` on. Defaults to 8080.
    ws_port : int, optional
        WebSocket port the bridge relays instrument data on. Defaults to 8765.
    udp_port : int, optional
        UDP port the bridge listens on for :class:`~instrumation.utils.DataBroadcaster`
        packets. Defaults to 9999.
    host : str, optional
        Bind address for all three servers. Defaults to ``"127.0.0.1"``.
    dist_dir : str, optional
        Path to the built ``vfp-dashboard`` React app (``npm run build`` output).
        Defaults to the ``vfp-dashboard/dist`` directory next to the repo root.

    Returns
    -------
    DashboardHandle
        Handle exposing ``.stop()`` for a clean shutdown of all servers.
    """
    bridge = VFPBridge(udp_host=host, udp_port=udp_port, ws_host=host, ws_port=ws_port)

    loop = asyncio.new_event_loop()

    def run_bridge():
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(bridge.start())
        except (asyncio.CancelledError, RuntimeError):
            pass
        finally:
            loop.close()

    bridge_thread = threading.Thread(target=run_bridge, daemon=True, name="vfp-bridge")
    bridge_thread.start()

    handler_cls = _make_request_handler(bridge, dist_dir)
    http_server = ThreadingHTTPServer((host, http_port), handler_cls)
    http_thread = threading.Thread(target=http_server.serve_forever, daemon=True, name="vfp-http")
    http_thread.start()

    logger.info(
        "VFP dashboard running: http://%s:%d (ws://%s:%d, udp:%d)",
        host, http_port, host, ws_port, udp_port,
    )

    return DashboardHandle(bridge, http_server, loop, bridge_thread, http_thread)
