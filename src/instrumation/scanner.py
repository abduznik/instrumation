import pyvisa
import serial.tools.list_ports

def scan():
    """
    Scans for both Serial ports (Control Box) and VISA instruments.
    Returns a list of dictionaries with device info.
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
        rm = pyvisa.ResourceManager()
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
