"""Device discovery across serial ports and VISA resources.

Enumerates what is physically attached -- serial ports via ``pyserial`` and VISA
resources via the shared resource manager -- and reports bus address conflicts
found in the result.
"""

import serial.tools.list_ports
from typing import Dict, List

def scan() -> List[Dict[str, str]]:
    """Enumerate attached serial ports and VISA instruments.

    Serial ports are always scanned. The VISA scan is attempted afterwards and
    skipped with a printed warning if the resource manager is unavailable, so a
    machine with no VISA backend still returns its serial devices.

    Returns
    -------
    list of dict
        One dict per device, each with keys:

        ``type``
            ``"serial"`` or ``"visa"``.
        ``id``
            The address -- a port path such as ``"COM3"`` or ``"/dev/ttyUSB0"``
            for serial devices, or a VISA resource string for VISA devices.
        ``desc``
            The port description for serial devices, or the literal
            ``"VISA Instrument"`` for VISA devices.

    Notes
    -----
    A VISA scan failure is reported on stdout rather than raised, so an empty
    or serial-only result does not necessarily mean nothing is connected.

    Examples
    --------
    >>> for dev in scan():
    ...     print(dev["type"], dev["id"], dev["desc"])
    """
    found_devices = []

    # 1. Scan for Serial Ports (Your Control Box)
    ports = serial.tools.list_ports.comports()
    for port in ports:
        found_devices.append({
            "type": "serial",
            "id": port.device,       # e.g., '/dev/ttyUSB0' or 'COM3'
            "desc": port.description
        })

    # 2. Scan for VISA Instruments (Keysight, etc.)
    try:
        from .factory import get_rm
        rm = get_rm()
        resources = rm.list_resources()
        for res in resources:
            found_devices.append({
                "type": "visa",
                "id": res,               # e.g., 'USB0::0x2A8D::...'
                "desc": "VISA Instrument"
            })
    except Exception as e:
        print(f"VISA scan warning: {e}")

    return found_devices


def find_duplicate_addresses(devices: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Find addresses that appear more than once with different identities.

    On shared buses (GPIB, RS-485), two instruments configured with the same
    address will corrupt each other's responses.  This function flags addresses
    that show up multiple times in a scan result with differing descriptions,
    which is the telltale sign of a bus conflict.

    Steps:
        1. Build a dict mapping each device "id" (address) to a list of its
           "desc" values across all scan results.
        2. For each address that has more than one distinct description:
           a. Create a conflict entry with:
              - "address": the duplicated address string
              - "identities": the list of distinct descriptions seen
              - "count": how many times it appeared
           b. Append it to the results list.
        3. Return the list of conflict entries. Empty list means no conflicts.

    Args:
        devices: The list of device dicts returned by scan(), each having
            keys "type", "id", and "desc".

    Returns:
        A list of dicts, each with keys "address" (str), "identities" (list
        of str), and "count" (int).  Empty list if no duplicates found.

    Example:
        >>> devices = scan()
        >>> conflicts = find_duplicate_addresses(devices)
        >>> for c in conflicts:
        ...     print(f"CONFLICT on {c['address']}: {c['identities']}")
    """
    from collections import defaultdict

    addr_to_descs = defaultdict(list)
    for device in devices:
        addr_to_descs[device["id"]].append(device["desc"])

    conflicts = []
    for addr, descs in addr_to_descs.items():
        unique_descs = list(set(descs))
        if len(unique_descs) > 1:
            conflicts.append({
                "address": addr,
                "identities": unique_descs,
                "count": len(descs),
            })

    return conflicts
