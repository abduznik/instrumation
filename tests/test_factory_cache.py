import json

from instrumation import factory


def test_read_creates_cache_when_missing(tmp_path, monkeypatch):
    """First read creates the cache file with an empty list and returns []."""
    cache = tmp_path / ".visa_cache.json"
    monkeypatch.setattr(factory, "CACHE_FILE", cache)

    assert factory._read_visa_cache() == []
    assert cache.exists()
    assert json.loads(cache.read_text()) == []


def test_write_then_read_roundtrip(tmp_path, monkeypatch):
    """A written cache is read back, most-recent first."""
    cache = tmp_path / ".visa_cache.json"
    monkeypatch.setattr(factory, "CACHE_FILE", cache)

    factory._write_visa_cache(["TCPIP0::1.2.3.4", "USB0::0x1"])
    assert factory._read_visa_cache() == ["TCPIP0::1.2.3.4", "USB0::0x1"]


def test_write_keeps_only_top_ten(tmp_path, monkeypatch):
    """Only the first 10 resources are persisted."""
    cache = tmp_path / ".visa_cache.json"
    monkeypatch.setattr(factory, "CACHE_FILE", cache)

    factory._write_visa_cache([f"RES{i}" for i in range(20)])
    assert factory._read_visa_cache() == [f"RES{i}" for i in range(10)]


def test_read_recovers_from_corrupt_cache(tmp_path, monkeypatch):
    """A corrupt cache degrades to an empty list instead of raising."""
    cache = tmp_path / ".visa_cache.json"
    cache.write_text("{ not valid json")
    monkeypatch.setattr(factory, "CACHE_FILE", cache)

    assert factory._read_visa_cache() == []


def test_read_after_external_delete(tmp_path, monkeypatch):
    """Deleting the file mid-run does not raise; it is recreated empty."""
    cache = tmp_path / ".visa_cache.json"
    monkeypatch.setattr(factory, "CACHE_FILE", cache)

    factory._write_visa_cache(["USB0::0x1"])
    cache.unlink()
    assert factory._read_visa_cache() == []
    assert cache.exists()
