import csv
import io
import json
import time
import urllib.request

import pytest

from instrumation.dashboard import launch_dashboard


def _free_ports(n=3):
    import socket

    socks = [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for _ in range(n)]
    for s in socks:
        s.bind(("127.0.0.1", 0))
    ports = [s.getsockname()[1] for s in socks]
    for s in socks:
        s.close()
    return ports


@pytest.fixture
def dashboard(tmp_path):
    http_port, ws_port, udp_port = _free_ports()
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "index.html").write_text("<html>vfp</html>")

    handle = launch_dashboard(
        http_port=http_port, ws_port=ws_port, udp_port=udp_port, dist_dir=str(dist_dir)
    )
    time.sleep(0.2)
    yield handle, http_port
    handle.stop()


def test_launch_dashboard_serves_static_index(dashboard):
    handle, http_port = dashboard
    with urllib.request.urlopen(f"http://127.0.0.1:{http_port}/") as resp:
        body = resp.read().decode()
    assert "vfp" in body


def test_readings_endpoint_json_empty(dashboard):
    handle, http_port = dashboard
    with urllib.request.urlopen(f"http://127.0.0.1:{http_port}/api/readings") as resp:
        data = json.loads(resp.read().decode())
    assert data == []


def test_readings_endpoint_csv_empty(dashboard):
    handle, http_port = dashboard
    with urllib.request.urlopen(f"http://127.0.0.1:{http_port}/api/readings?format=csv") as resp:
        body = resp.read().decode()
    rows = list(csv.reader(io.StringIO(body)))
    assert rows[0] == ["instrument", "parameter", "value", "unit", "timestamp"]
    assert len(rows) == 1


def test_readings_endpoint_reflects_bridge_data(dashboard):
    handle, http_port = dashboard
    handle.bridge.latest_readings["DMM1@TCPIP::1"] = {
        "value": 3.3,
        "unit": "V",
        "timestamp": "2026-09-13T00:00:00",
        "metadata": {"instrument_id": "DMM1@TCPIP::1", "driver": "Keysight34461A"},
    }

    with urllib.request.urlopen(f"http://127.0.0.1:{http_port}/api/readings") as resp:
        data = json.loads(resp.read().decode())

    assert len(data) == 1
    assert data[0]["instrument"] == "DMM1@TCPIP::1"
    assert data[0]["value"] == 3.3
    assert data[0]["unit"] == "V"


def test_stop_shuts_down_cleanly(tmp_path):
    http_port, ws_port, udp_port = _free_ports()
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()

    handle = launch_dashboard(
        http_port=http_port, ws_port=ws_port, udp_port=udp_port, dist_dir=str(dist_dir)
    )
    time.sleep(0.2)
    handle.stop()

    assert not handle._bridge_thread.is_alive()
    assert not handle._http_thread.is_alive()
