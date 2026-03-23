"""
instrumation CLI
================
A command-line interface for the instrumation library.

Usage examples
--------------
  # Discover all instruments on the bench
  instrumation scan

  # Print the IDN string of a specific instrument
  instrumation identify --address USB0::0x2A8D::0x1301::MY001::INSTR

  # Take a single measurement (works in SIM mode too)
  instrumation measure --address USB0::0x2A8D::... --type DMM --param voltage
  instrumation measure --address USB0::0x2A8D::... --type SA  --param peak
  instrumation measure --address USB0::0x2A8D::... --type PSU --param current

  # Stream live readings over UDP (integrates with DataBroadcaster)
  instrumation broadcast --address USB0::... --type SA --param peak \\
                         --host 127.0.0.1 --port 5005 --interval 1.0 --count 10

Set INSTRUMATION_MODE=SIM to run everything against the simulated drivers.
"""

import argparse
import json
import sys
import time

from .config import is_sim_mode


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DRIVER_TYPES = ("DMM", "PSU", "SA", "NA", "SCOPE")

# Maps (driver_type, param) -> lambda that calls the right method
_MEASURE_DISPATCH = {
    ("DMM", "voltage"):    lambda d: d.measure_voltage(),
    ("DMM", "resistance"): lambda d: d.measure_resistance(),
    ("DMM", "frequency"):  lambda d: d.measure_frequency(),
    ("DMM", "duty-cycle"): lambda d: d.measure_duty_cycle(),
    ("DMM", "vpp"):        lambda d: d.measure_v_peak_to_peak(),
    ("PSU", "current"):    lambda d: d.get_current(),
    ("SA",  "peak"):       lambda d: d.get_peak_value(),
    ("SCOPE", "frequency"): lambda d: d.measure_frequency(),
    ("SCOPE", "vpp"):       lambda d: d.measure_v_peak_to_peak(),
    ("SCOPE", "waveform"):  lambda d: d.get_waveform(1),
}

_PARAM_UNITS = {
    "voltage":    "V",
    "resistance": "Ω",
    "frequency":  "Hz",
    "duty-cycle": "%",
    "vpp":        "V",
    "current":    "A",
    "peak":       "dBm",
    "waveform":   "(samples)",
}


def _get_driver(address, driver_type):
    """Return a connected instrument driver (sim or real)."""
    from .factory import get_instrument
    driver = get_instrument(address, driver_type)
    driver.connect()
    return driver


def _print_table(devices):
    if not devices:
        print("  (none found)")
        return
    col_type = max(len(d["type"]) for d in devices)
    col_id   = max(len(d["id"])   for d in devices)
    header = f"  {'TYPE':<{col_type}}  {'ADDRESS / PORT':<{col_id}}  DESCRIPTION"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for d in devices:
        print(f"  {d['type']:<{col_type}}  {d['id']:<{col_id}}  {d['desc']}")


# ---------------------------------------------------------------------------
# Sub-command handlers
# ---------------------------------------------------------------------------

def cmd_scan(_args):
    """Discover VISA instruments and serial ports."""
    if is_sim_mode():
        print("[SIM] Hardware scan skipped in simulation mode.")
        print("      Use --address with any dummy string + --type to measure.")
        return 0

    from .scanner import scan
    print("Scanning for instruments...")
    devices = scan()
    print(f"\nFound {len(devices)} device(s):\n")
    _print_table(devices)
    return 0


def cmd_identify(args):
    """Print the *IDN? string of an instrument."""
    if is_sim_mode():
        driver = _get_driver(args.address, "DMM")
        print(f"ID: {driver.get_id()}")
        driver.disconnect()
        return 0

    import pyvisa
    try:
        rm = pyvisa.ResourceManager()
        res = rm.open_resource(args.address)
        idn = res.query("*IDN?").strip()
        res.close()
        print(f"ID: {idn}")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_measure(args):
    """Take a single measurement and print the result."""
    key = (args.type.upper(), args.param.lower())
    if key not in _MEASURE_DISPATCH:
        valid = [p for t, p in _MEASURE_DISPATCH if t == args.type.upper()]
        print(
            f"Error: --param '{args.param}' is not valid for --type '{args.type}'.\n"
            f"Valid params for {args.type.upper()}: {', '.join(valid) or 'none'}",
            file=sys.stderr,
        )
        return 1

    try:
        if args.json:
            # Suppress driver connect/disconnect chatter so stdout is pure JSON
            import io
            from contextlib import redirect_stdout
            _sink = io.StringIO()
            with redirect_stdout(_sink):
                driver = _get_driver(args.address, args.type.upper())
                value  = _MEASURE_DISPATCH[key](driver)
                driver.disconnect()
        else:
            driver = _get_driver(args.address, args.type.upper())
            value  = _MEASURE_DISPATCH[key](driver)
            driver.disconnect()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    unit = _PARAM_UNITS.get(args.param.lower(), "")

    if isinstance(value, list):
        if args.json:
            print(json.dumps(value))
        else:
            print(f"{args.param}: [{', '.join(f'{v:.4f}' for v in value[:8])}{'...' if len(value) > 8 else ''}]  {unit}")
    else:
        if args.json:
            print(json.dumps({args.param: value}))
        else:
            print(f"{args.param}: {value:.6g} {unit}")
    return 0


def cmd_broadcast(args):
    """Stream instrument readings over UDP using DataBroadcaster."""
    key = (args.type.upper(), args.param.lower())
    if key not in _MEASURE_DISPATCH:
        valid = [p for t, p in _MEASURE_DISPATCH if t == args.type.upper()]
        print(
            f"Error: --param '{args.param}' is not valid for --type '{args.type}'.\n"
            f"Valid params for {args.type.upper()}: {', '.join(valid) or 'none'}",
            file=sys.stderr,
        )
        return 1

    from .utils import DataBroadcaster

    try:
        driver = _get_driver(args.address, args.type.upper())
    except Exception as exc:
        print(f"Error connecting: {exc}", file=sys.stderr)
        return 1

    count     = args.count   # 0 = infinite
    interval  = args.interval
    sent      = 0

    print(
        f"Broadcasting {args.type.upper()}/{args.param} -> "
        f"udp://{args.host}:{args.port}  (interval={interval}s"
        + (f", count={count}" if count else ", Ctrl-C to stop")
        + ")"
    )

    with DataBroadcaster(host=args.host, port=args.port) as broadcaster:
        try:
            while count == 0 or sent < count:
                value = _MEASURE_DISPATCH[key](driver)
                payload = {
                    "type":  args.type.upper(),
                    "param": args.param.lower(),
                    "value": value,
                    "unit":  _PARAM_UNITS.get(args.param.lower(), ""),
                    "ts":    time.time(),
                }
                broadcaster.send(payload)
                print(f"  sent: {json.dumps(payload)}")
                sent += 1
                if count == 0 or sent < count:
                    time.sleep(interval)
        except KeyboardInterrupt:
            print("\nStopped.")

    driver.disconnect()
    return 0


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def _build_parser():
    parser = argparse.ArgumentParser(
        prog="instrumation",
        description="Command-line interface for the instrumation library.\n"
                    "Set INSTRUMATION_MODE=SIM to use simulated drivers.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # ---- scan ----
    sub.add_parser(
        "scan",
        help="Discover VISA instruments and serial ports on this machine.",
    )

    # ---- identify ----
    p_id = sub.add_parser(
        "identify",
        help="Print the *IDN? string of an instrument.",
    )
    p_id.add_argument("--address", required=True, metavar="ADDR",
                      help="VISA address, e.g. USB0::0x2A8D::0x1301::MY001::INSTR")

    # ---- measure ----
    p_meas = sub.add_parser(
        "measure",
        help="Take a single measurement and print the result.",
    )
    p_meas.add_argument("--address", required=True, metavar="ADDR",
                        help="VISA address or SIM dummy string")
    p_meas.add_argument("--type", required=True, choices=DRIVER_TYPES,
                        metavar="TYPE",
                        help=f"Instrument type: {', '.join(DRIVER_TYPES)}")
    p_meas.add_argument("--param", required=True, metavar="PARAM",
                        help="What to measure: voltage, resistance, frequency, "
                             "duty-cycle, vpp, current, peak, waveform")
    p_meas.add_argument("--json", action="store_true",
                        help="Output as JSON instead of human-readable text")

    # ---- broadcast ----
    p_bc = sub.add_parser(
        "broadcast",
        help="Stream live readings over UDP using DataBroadcaster.",
    )
    p_bc.add_argument("--address", required=True, metavar="ADDR",
                      help="VISA address or SIM dummy string")
    p_bc.add_argument("--type", required=True, choices=DRIVER_TYPES,
                      metavar="TYPE",
                      help=f"Instrument type: {', '.join(DRIVER_TYPES)}")
    p_bc.add_argument("--param", required=True, metavar="PARAM",
                      help="Measurement parameter (same as 'measure')")
    p_bc.add_argument("--host", default="127.0.0.1",
                      help="UDP destination host (default: 127.0.0.1)")
    p_bc.add_argument("--port", type=int, default=5005,
                      help="UDP destination port (default: 5005)")
    p_bc.add_argument("--interval", type=float, default=1.0,
                      help="Seconds between readings (default: 1.0)")
    p_bc.add_argument("--count", type=int, default=0,
                      help="Number of readings to send; 0 = infinite (default: 0)")

    return parser


_DISPATCH = {
    "scan":      cmd_scan,
    "identify":  cmd_identify,
    "measure":   cmd_measure,
    "broadcast": cmd_broadcast,
}


def main(argv=None):
    parser = _build_parser()
    args   = parser.parse_args(argv)
    handler = _DISPATCH[args.command]
    sys.exit(handler(args))


if __name__ == "__main__":
    main()
