from instrumation.scanner import find_duplicate_addresses


def test_find_duplicate_addresses_empty_list():
    """Empty input returns an empty list."""
    assert find_duplicate_addresses([]) == []


def test_find_duplicate_addresses_none_input():
    """None input returns an empty list instead of raising."""
    assert find_duplicate_addresses(None) == []


def test_find_duplicate_addresses_single_device():
    """A single device can never conflict with itself."""
    devices = [{"type": "scope", "id": "GPIB0::1", "desc": "Scope A"}]
    assert find_duplicate_addresses(devices) == []


def test_find_duplicate_addresses_all_same_identity():
    """Same address repeated with the identical description is not a conflict."""
    devices = [
        {"type": "scope", "id": "GPIB0::1", "desc": "Scope A"},
        {"type": "scope", "id": "GPIB0::1", "desc": "Scope A"},
    ]
    assert find_duplicate_addresses(devices) == []


def test_find_duplicate_addresses_real_conflict():
    """Same address with differing descriptions is flagged as a conflict."""
    devices = [
        {"type": "scope", "id": "GPIB0::1", "desc": "Scope A"},
        {"type": "load", "id": "GPIB0::1", "desc": "Load B"},
    ]
    conflicts = find_duplicate_addresses(devices)
    assert len(conflicts) == 1
    assert conflicts[0]["address"] == "GPIB0::1"
    assert conflicts[0]["count"] == 2
    assert sorted(conflicts[0]["identities"]) == ["Load B", "Scope A"]
