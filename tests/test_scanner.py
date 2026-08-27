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


def test_find_duplicate_addresses_same_desc_different_type():
    """Same address + identical description but different device types is still a
    conflict -- two genuinely different physical devices sharing a description."""
    devices = [
        {"type": "scope", "id": "GPIB0::1", "desc": "Bench Instrument"},
        {"type": "load", "id": "GPIB0::1", "desc": "Bench Instrument"},
    ]
    conflicts = find_duplicate_addresses(devices)
    assert len(conflicts) == 1
    assert conflicts[0]["address"] == "GPIB0::1"
    assert conflicts[0]["count"] == 2
    assert conflicts[0]["identities"] == ["Bench Instrument"]


def test_find_duplicate_addresses_same_desc_same_type_no_conflict():
    """Same address + identical description + same type is a single device
    reported repeatedly (e.g. duplicate scan entries), not a conflict."""
    devices = [
        {"type": "psu", "id": "GPIB0::5", "desc": "PSU X"},
        {"type": "psu", "id": "GPIB0::5", "desc": "PSU X"},
    ]
    assert find_duplicate_addresses(devices) == []


def test_find_duplicate_addresses_three_devices_two_identities():
    """Three entries on one address with two distinct identities -> one conflict
    with count 3 and the two identities reported."""
    devices = [
        {"type": "scope", "id": "GPIB0::3", "desc": "Alpha"},
        {"type": "scope", "id": "GPIB0::3", "desc": "Alpha"},
        {"type": "dmm", "id": "GPIB0::3", "desc": "Beta"},
    ]
    conflicts = find_duplicate_addresses(devices)
    assert len(conflicts) == 1
    assert conflicts[0]["count"] == 3
    assert sorted(conflicts[0]["identities"]) == ["Alpha", "Beta"]


def test_find_duplicate_addresses_multiple_conflicts():
    """Conflicts on different addresses are all reported independently."""
    devices = [
        {"type": "scope", "id": "GPIB0::1", "desc": "Scope A"},
        {"type": "load", "id": "GPIB0::1", "desc": "Load B"},
        {"type": "sa", "id": "GPIB0::2", "desc": "SA C"},
        {"type": "sa", "id": "GPIB0::2", "desc": "SA D"},
        {"type": "psu", "id": "GPIB0::9", "desc": "PSU"},
    ]
    conflicts = find_duplicate_addresses(devices)
    assert len(conflicts) == 2
    assert {c["address"] for c in conflicts} == {"GPIB0::1", "GPIB0::2"}
