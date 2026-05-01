import argparse
import sys
import os
from .scanner import scan
from .factory import get_instrument
from .station import Station

def handle_scan(args):
    print("Scanning for instruments...")
    devices = scan()
    if not devices:
        print("No devices found.")
        return
    
    print(f"{'TYPE':<10} {'ID':<30} {'DESCRIPTION'}")
    print("-" * 60)
    for dev in devices:
        print(f"{dev['type']:<10} {dev['id']:<30} {dev['desc']}")

def handle_measure(args):
    try:
        with get_instrument(args.address, args.type) as instr:
            method = getattr(instr, args.method)
            result = method()
            print(f"Result: {result}")
    except Exception as e:
        print(f"Error during measurement: {e}")
        sys.exit(1)

def handle_station_list(args):
    config_path = args.config if args.config else "station.toml"
    if not os.path.exists(config_path):
        print(f"Error: Station config '{config_path}' not found.")
        return
    
    station = Station(config_path)
    print(f"Station: {config_path}")
    print(f"{'NAME':<15} {'TYPE':<10} {'ADDRESS'}")
    print("-" * 45)
    # Since Station doesn't expose the config easily, we reload it here or use the objects
    # But for now, we'll just show what's in the instruments dict
    for name, inst in station.instruments.items():
        # We don't have the original 'type' string easily available from the instance 
        # unless we add it. For now, we'll show the class name.
        type_name = inst.__class__.__name__
        print(f"{name:<15} {type_name:<10} {inst.resource}")

def handle_station_measure(args):
    config_path = args.config if args.config else "station.toml"
    station = Station(config_path)
    
    if args.name not in station.instruments:
        print(f"Error: Instrument '{args.name}' not found in station.")
        sys.exit(1)
        
    instr = station.instruments[args.name]
    try:
        instr.connect()
        method = getattr(instr, args.method)
        result = method()
        print(f"[{args.name}] Result: {result}")
        instr.disconnect()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(prog="instrumation", description="Instrumation CLI - RF Test Station HAL")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Scan command
    subparsers.add_parser("scan", help="Scan for available instruments")

    # Measure command
    measure_parser = subparsers.add_parser("measure", help="Take a one-off measurement")
    measure_parser.add_argument("address", help="Instrument address (VISA or Serial)")
    measure_parser.add_argument("type", help="Instrument type (DMM, PSU, SA, NA, SCOPE)")
    measure_parser.add_argument("method", help="Method to call (e.g., measure_voltage)")

    # Station command
    station_parser = subparsers.add_parser("station", help="Manage and use a station")
    station_subparsers = station_parser.add_subparsers(dest="subcommand", help="Station subcommand")
    
    list_parser = station_subparsers.add_parser("list", help="List instruments in the station")
    list_parser.add_argument("-c", "--config", help="Path to station.toml")
    
    st_measure_parser = station_subparsers.add_parser("measure", help="Measure using a station instrument")
    st_measure_parser.add_argument("name", help="Name of the instrument in the station")
    st_measure_parser.add_argument("method", help="Method to call")
    st_measure_parser.add_argument("-c", "--config", help="Path to station.toml")

    args = parser.parse_args()

    if args.command == "scan":
        handle_scan(args)
    elif args.command == "measure":
        handle_measure(args)
    elif args.command == "station":
        if args.subcommand == "list":
            handle_station_list(args)
        elif args.subcommand == "measure":
            handle_station_measure(args)
        else:
            station_parser.print_help()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
