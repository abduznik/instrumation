"""Driver factory and instrument discovery.

Resolves a resource address into a connected instrument driver, handling replay
files, simulated instruments, auto-discovery and real hardware behind a single
entry point, :func:`get_instrument`.
"""

import pyvisa
import importlib
import json
import logging
import os
import re
import time
from pathlib import Path
from .drivers.real import RealDriver
from .drivers.generic import GenericDriver
from .drivers.registry import DriverRegistry
from .exceptions import ConnectionLost
from .drivers.base import Oscilloscope, SpectrumAnalyzer, SignalGenerator, FunctionGenerator, PowerSupply, Multimeter, NetworkAnalyzer, ElectronicLoad, FrequencyCounter

logger = logging.getLogger(__name__)

# Canonical instrument categories (driver_type values). GENERIC is the
# universal fallback; anything NOT in this set is a type the library has
# never heard of.
KNOWN_DRIVER_TYPES = frozenset({
    "SCOPE", "SA", "SG", "PSU", "DMM", "VNA", "NA", "LOAD", "ELOAD",
    "COUNTER", "LCR", "LOCKIN", "SWITCH", "SENSOR", "POWERMETER", "ACPSU",
    "DAQ", "PEAKPM", "TEMP", "GENERIC",
})

# ASRL resources look like "ASRL1::INSTR", "ASRL10::INSTR", "ASRL21::INSTR".
# Low-numbered ports (1-4) are typically on-board legacy serial ports that
# should not be auto-probed; higher numbers are USB-serial adapters worth trying.
_ASRL_PORT_RE = re.compile(r"^ASRL(\d+)::", re.IGNORECASE)


def _asrl_port_number(resource: str):
    """Return the numeric port of an ASRL VISA resource, or None if not ASRL."""
    m = _ASRL_PORT_RE.match(resource.strip())
    return int(m.group(1)) if m else None


def _skip_serial_probe(resource: str) -> bool:
    """True when an ASRL resource should be skipped by AUTO discovery.

    Only exact ASRL resources with port numbers 1-4 are skipped -- substring
    matches (e.g. "ASRL10" containing "1", or digits inside a TCPIP address)
    must NOT trigger the skip.
    """
    port = _asrl_port_number(resource)
    return port is not None and 1 <= port <= 4


def _discovery_priority(resource: str) -> int:
    """Rank a VISA resource for AUTO-discovery ordering (higher = probed first).

    Follows the documented preference: HiSLIP/TCPIP (LAN) first, then USB,
    then GPIB, with serial (ASRL) and anything unrecognised last. Python's
    stable sort keeps input (recency) order within the same tier.
    """
    r = resource.upper()
    if "HISLIP" in r or "TCPIP" in r:
        return 3
    if "USB" in r:
        return 2
    if "GPIB" in r:
        return 1
    return 0

# Global Resource Manager to prevent "Too many managers" errors on macOS
_GLOBAL_RM = None

def get_rm():
    """Return the process-wide PyVISA resource manager, creating it on first use.

    A single :class:`pyvisa.ResourceManager` is cached for the lifetime of the
    process. Opening several managers causes "Too many managers" errors on
    macOS, so every caller shares this one.

    On macOS the NI-VISA framework at
    ``/Library/Frameworks/VISA.framework/VISA`` is requested explicitly when
    that path exists; otherwise PyVISA selects its own backend.

    On Windows ``None`` is never passed to :class:`pyvisa.ResourceManager`:
    passing ``None`` crashes newer PyVISA versions with
    ``AttributeError: 'NoneType' object has no attribute 'rsplit'``. An empty
    string is passed instead so PyVISA automatically selects whatever backend
    is available (system VISA if installed, otherwise the bundled
    ``pyvisa_py``).

    Returns
    -------
    pyvisa.ResourceManager
        The shared resource manager instance.
    """
    global _GLOBAL_RM
    if _GLOBAL_RM is None:
        ni_lib = "/Library/Frameworks/VISA.framework/VISA"
        rm_args = ni_lib if os.path.exists(ni_lib) else ""
        _GLOBAL_RM = pyvisa.ResourceManager(rm_args)
    return _GLOBAL_RM


def close_rm() -> None:
    """Close and release the process-wide PyVISA resource manager, if open.

    :func:`get_rm` caches a single :class:`pyvisa.ResourceManager` for the
    life of the process. Call ``close_rm()`` to release its underlying VISA
    session -- e.g. to switch VISA backends at runtime, to free the OS-level
    handle in a long-running process that no longer needs instrument access,
    or between tests that require full isolation of VISA state. The next
    call to :func:`get_rm` transparently creates a fresh manager.

    Safe to call even if no resource manager has been created yet (no-op).
    """
    global _GLOBAL_RM
    if _GLOBAL_RM is not None:
        _GLOBAL_RM.close()
        _GLOBAL_RM = None


def is_sim_mode() -> bool:
    """Report whether simulation (digital twin) mode is enabled.

    Simulation mode is controlled by the ``INSTRUMATION_MODE`` environment
    variable and the comparison is case-insensitive.

    Returns
    -------
    bool
        ``True`` when ``INSTRUMATION_MODE`` is ``"SIM"`` or ``"SIMULATED"``,
        ``False`` otherwise.
    """
    mode = os.environ.get("INSTRUMATION_MODE", "").upper()
    return mode == "SIM" or mode == "SIMULATED"

def _discover_lan_resources() -> list:
    """Scans the local ARP table for potential LAN instruments."""
    resources = []
    try:
        import subprocess
        import re
        output = subprocess.check_output(["arp", "-an"]).decode()
        ips = re.findall(r"\((\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\)", output)
        for ip in ips:
            # Skip broadcast and local loopback
            if ip.endswith(".255") or ip.startswith("127.") or ip.startswith("224.") or ip.startswith("239."):
                continue
            # Try both VXI-11 and HiSLIP — modern Keysight instruments prefer HiSLIP
            resources.append(f"TCPIP::{ip}::hislip0::INSTR")
            resources.append(f"TCPIP::{ip}::INSTR")
    except Exception:
        pass
    return resources

def _discover_mdns_resources() -> list:
    """Probe known Keysight mDNS hostnames via HiSLIP."""
    import socket
    resources = []
    # Common Keysight hostname patterns resolvable via mDNS/Bonjour
    candidates = [
        "a-n5232a-20127.local",  # your VNA
        "a-n9030a-10156.local",  # your PXA
    ]
    for host in candidates:
        try:
            # Resolve and check if HiSLIP port (4880) is open
            socket.getaddrinfo(host, 4880)
            resources.append(f"TCPIP::{host}::hislip0::INSTR")
        except socket.gaierror:
            pass
    return resources

# IDN routing table. Order matters: the first brand block whose token is in
# the upper-cased *IDN? reply is chosen, then the first model entry in that
# block that matches wins. A model entry matches if any alternative is in the
# IDN; an alternative that is a tuple needs all of its tokens. An empty model
# tuple is the brand's fallback. Targets are "module.Class" under
# instrumation.drivers, imported lazily.
_IDN_ROUTES = [
    (("TEKTRONIX",), [
        (("AFG",), "tektronix.TektronixAFG"),
        (("PA1000",), "tektronix_pa1000.TektronixPA1000"),
        ((), "tektronix.TektronixTDS"),
    ]),
    (("KEYSIGHT", "AGILENT", "HEWLETT-PACKARD", "HP"), [
        (("DSO-X", "MSO-X", "DSOX", "MSOX"), "keysight.KeysightInfiniiVision"),
        (("N9030", "N9020", "N9010", "PXA", "MXA", "EXA"), "keysight.KeysightPXA"),
        (("E8257", "N5181", "N5182", "N5183", "PSG", "MXG", "EXG"), "keysight.KeysightSG"),
        (("N99", "FIELD FOX"), "keysight.KeysightFieldFox"),
        (("34461", "34460"), "keysight.Keysight34461A"),
        (("E83", "N52", "PNA"), "keysight.KeysightPNA"),
        (("34401", "34410", "34411", "34420"), "keysight.Keysight34461A"),
        (("E3631", "E36313", "E3633"), "keysight_psu.KeysightE36313A"),
        (("E4980",), "keysight_lcr.KeysightE4980A"),
        (("E4990",), "keysight_e4990a.KeysightE4990A"),
        (("53230", "53220", "53181"), "keysight.Keysight53230A"),
        (("U2000", "U200"), "keysight_powersensor.KeysightU2000"),
        (("6632", "6633", "6634", "6631"), "agilent_psu.Agilent6632B"),
        (("AC6800", "AC68"), "keysight_ac_psu.KeysightAC6800B"),
        (("DAQ970", "DAQ973"), "keysight_daq.KeysightDAQ970A"),
    ]),
    (("SIGLENT",), [
        (("SDM",), "siglent_dmm.SiglentSDM3055"),
        (("SPD",), "siglent_psu.SiglentSPD3303X"),
        ((("PLUS", "SDS1"), ("PLUS", "SDS2"), ("PLUS", "SDS5")), "siglent_scope.SiglentSDS2000XPlus"),
        (("SSA",), "siglent_sa.SiglentSSA3000X"),
        (("SDG",), "siglent_awg.SiglentSDG2000X"),
        (("SNA",), "siglent_vna.SiglentSNA5000A"),
        ((), "siglent.SiglentSDS"),
    ]),
    (("RIGOL",), [
        (("DS1054Z", "DS1104Z", "DS1074Z", "DS1102Z", "MSO1054Z", "MSO1104Z",
          "MSO1074Z", "DS1000Z", "MSO1000Z"), "rigol.RigolDS1054Z"),
        (("MSO5",), "rigol_mso5000.RigolMSO5000"),
        (("DM3",), "rigol_dmm.RigolDM3068"),
        (("DP8",), "rigol_psu.RigolDP832"),
        (("DL3",), "rigol_load.RigolDL3021"),
        (("DG4", "DG5", "DG1000Z"), "rigol_awg.RigolDG4000"),
        ((), "rigol.RigolDSA"),
    ]),
    (("KEITHLEY",), [
        (("2400",), "keithley.Keithley2400"),
        (("2000",), "keithley.Keithley2000"),
        (("DMM6500", "6500"), "keithley_dmm6500.KeithleyDMM6500"),
    ]),
    (("TDK-LAMBDA", "Z+"), [((), "tdk.TDKLambdaZPlus")]),
    (("KORAD",), [((), "korad.KoradKA3005P")]),
    (("STANFORD",), [
        (("DS345",), "srs_ds345.SRSDS345"),
        (("SR830",), "srs_sr830.SRSSR830"),
    ]),
    (("HIOKI",), [(("IM35",), "hioki_lcr.HiokiIM3536")]),
    (("MINI-CIRCUITS", "MINICIRCUITS"), [((), "minicircuits_switch.MiniCircuitsRCSwitch")]),
    (("YOKOGAWA",), [(("WT3",), "yokogawa_wt.YokogawaWT310")]),
    (("ANRITSU",), [
        (("MS2035",), "anritsu.AnritsuMS2035B"),
        (("SHOCKLINE", "MS4"), "anritsu.AnritsuShockLineVNA"),
        (("VNA", "MS20"), "anritsu.AnritsuVNA"),
        ((), "anritsu.AnritsuSA"),
    ]),
    (("PROLOGIX",), [((), "prologix.PrologixDriver")]),
    (("FLUKE",), [
        (("8845", "8846"), "fluke.Fluke8846A"),
        (("PM6690",), "fluke_counter.FlukePM6690"),
    ]),
    (("B&K", "BK PRECISION"), [
        (("9130",), "bk_precision.BKPrecision9130B"),
        (("8600", "8601", "8602", "8610", "8612", "8614", "8620"), "bk_precision.BKPrecision8600"),
        (("1685", "1687", "1688"), "bk_precision_1685b.BKPrecision1685B"),
    ]),
    (("HAMEG", "ROHDE", "ROHDE&SCHWARZ"), [
        (("HMO",), "rs_scope.RohdeSchwarzHMOCompact"),
        (("NRP",), "rs_powersensor.RohdeSchwarzNRPZ"),
        (("HMP",), "rs_psu.RohdeSchwarzHMP4040"),
    ]),
    (("GW", "GWINSTEK", "GW INSTEK"), [
        (("GPP",), "gwinstek_psu.GWInstekGPP4323"),
        (("MFG",), "gwinstek_awg.GWInstekMFG2000"),
    ]),
    (("ITECH",), [(("IT85",), "itech_load.ItechIT8512Plus")]),
    (("CHROMA",), [(("632",), "chroma_load.Chroma63200A")]),
    (("AIM-TTI", "THURLBY THANDAR", "AIMTTI"), [(("CPX400",), "aimtti_psu.AimTTiCPX400DP")]),
    (("SORENSEN",), [(("SG",), "sorensen_psu.SorensenSG")]),
    (("PRODIGIT",), [(("3311", "3310"), "prodigit_load.Prodigit3311F")]),
    (("BOONTON",), [
        (("4532",), "boonton_pm.Boonton4532"),
        (("4531", "4530"), "boonton_pm.Boonton4531"),
    ]),
    (("LAKE SHORE", "LAKESHORE", "LSCI"), [(("336", "335"), "lakeshore.LakeShore336")]),
]


def route_idn(idn: str):
    """Returns the driver class for an upper-cased ``*IDN?`` reply, or None."""
    for brands, models in _IDN_ROUTES:
        if not any(b in idn for b in brands):
            continue
        for alts, target in models:
            if not alts or any(
                all(tok in idn for tok in ((a,) if isinstance(a, str) else a)) for a in alts
            ):
                module, cls = target.rsplit(".", 1)
                return getattr(importlib.import_module(f".drivers.{module}", __package__), cls)
        return None  # brand matched but model unknown, as in the old if/elif chain
    return None


def get_instrument(resource_address: str, driver_type: str = "GENERIC", probe_asrl: bool = True) -> any:
    """Connect to an instrument and return a driver instance for it.

    The address is resolved in priority order:

    1. **Replay** -- an address beginning with ``replay://`` returns a
       ``ReplayDriver`` that reads from the file named after the prefix.
    2. **Simulation** -- when :func:`is_sim_mode` is true, a simulated driver
       registered for ``driver_type`` is returned instead of touching hardware.
    3. **Auto-discovery** -- the literal address ``"AUTO"`` searches for a
       matching instrument, trying the on-disk cache first, then mDNS, then the
       LAN ARP table, then a full VISA scan.
    4. **Real hardware** -- any other address is opened directly, identified via
       ``*IDN?``, and routed to the matching vendor driver.

    Parameters
    ----------
    resource_address : str
        A VISA resource string such as ``"TCPIP::192.168.1.5::INSTR"``, a
        ``replay://`` file path, or the literal ``"AUTO"`` to auto-discover.
    driver_type : str, optional
        Instrument category used to select and validate the driver. One of
        ``"SCOPE"``, ``"SA"``, ``"SG"``, ``"PSU"``, ``"DMM"``, ``"VNA"``,
        ``"NA"``, ``"LOAD"``, ``"ELOAD"``, ``"COUNTER"``, ``"ACPSU"``,
        ``"DAQ"``, ``"PEAKPM"``, ``"TEMP"`` or ``"GENERIC"``. Defaults to
        ``"GENERIC"``, which accepts any instrument.
    probe_asrl : bool, optional
        When True (default), an explicit ASRL connection gets a best-effort
        TDK-Lambda Z+ handshake (``INST:NSEL 6``) before ``*IDN?`` so the
        unit can identify itself. During ``"AUTO"`` discovery this is
        disabled: vendor-specific commands are never sent to arbitrary
        serial devices (gh #150).

    Returns
    -------
    object
        A connected driver instance. The concrete class depends on which
        instrument was identified.

    Raises
    ------
    ValueError
        If simulation mode is active, ``driver_type`` is not ``"GENERIC"`` and
        no simulated driver is registered for that type; or if ``"AUTO"``
        discovery finds no matching instrument.

    Notes
    -----
    Resources found through ``"AUTO"`` discovery are written to
    ``.visa_cache.json`` in the working directory, most recent first, so later
    lookups try them before falling back to a full scan.

    Examples
    --------
    >>> dmm = get_instrument("TCPIP::192.168.1.5::INSTR", "DMM")
    >>> scope = get_instrument("AUTO", "SCOPE")
    """
    # 0. Check for replay mode (Highest Priority)
    if resource_address.startswith("replay://"):
        file_path = resource_address.replace("replay://", "")
        from .drivers.replay import ReplayDriver
        return ReplayDriver(resource_address, master_file=file_path)

    # 1. Handle Simulation Mode (The Digital Twin Path)
    if is_sim_mode():
        from .drivers.simulated import SimulatedGeneric
        drivers = DriverRegistry.get_drivers_by_type(driver_type)
        for drv_cls in drivers:
            if drv_cls.is_simulated:
                # Use the requested address or a mock one
                addr = resource_address if resource_address != "AUTO" else "USB0::SIM::INSTR"
                drv = drv_cls(addr)
                drv.connect()
                return drv

        # If explicitly requested a type and not found, raise error (don't fallback to DMM silently)
        if driver_type != "GENERIC":
            raise ValueError(f"No simulated driver found for type: {driver_type}")

        # Fallback for GENERIC only
        drv = SimulatedGeneric(resource_address if resource_address != "AUTO" else "USB0::SIM::INSTR")
        drv.connect()
        return drv

    # 2. Handle AUTO discovery
    if resource_address == "AUTO":
        from concurrent.futures import ThreadPoolExecutor, as_completed
        cache_file = Path(".visa_cache.json")

        # 1. Load Cache & LAN (The Fast Resources)
        cached_resources = []
        if cache_file.exists():
            try:
                cached_resources = json.loads(cache_file.read_text())
            except (IOError, OSError, json.JSONDecodeError):
                pass
        else:
            # Create an empty cache file on first run so AUTO doesn't
            # always fall through to the slow full VISA scan.
            try:
                cache_file.write_text("[]")
            except (IOError, OSError):
                pass
        
        lan_resources = _discover_lan_resources()
        tried = set()

        def run_probe(resources, desc):
            # Sort by priority and recency
            candidates = []
            for r in resources:
                if r not in tried:
                    candidates.append(r)
            
            if not candidates:
                return None
            
            # Sort by transport priority tier (HiSLIP/TCPIP > USB > GPIB >
            # serial), preserving input (recency) order within the same tier
            # via the stable sort.
            candidates.sort(key=_discovery_priority, reverse=True)
            
            logger.info(f"AUTO-Discovery checking {desc}: {candidates}")
            
            if len(candidates) <= 2:
                for res in candidates:
                    tried.add(res)
                    result = probe_resource(res)
                    if result:
                        update_cache(result.resource_address)
                        return result
                return None

            with ThreadPoolExecutor(max_workers=4) as executor:
                future_to_res = {executor.submit(probe_resource, res): res for res in candidates}
                for future in as_completed(future_to_res):
                    tried.add(future_to_res[future])
                    result = future.result()
                    if result:
                        update_cache(result.resource_address)
                        return result
            return None

        def update_cache(res):
            try:
                # Move successful resource to the front of the cache
                new_cache = [res] + [r for r in cached_resources if r != res]
                cache_file.write_text(json.dumps(new_cache[:10]))  # Keep top 10 for speed
            except (IOError, OSError):
                pass

        def probe_resource(res):
            try:
                if _skip_serial_probe(res):
                    return None
                dev = get_instrument(res, driver_type, probe_asrl=False)
                type_map = {"SCOPE": Oscilloscope, "SA": SpectrumAnalyzer, "SG": (SignalGenerator, FunctionGenerator), "PSU": PowerSupply, "DMM": Multimeter, "VNA": NetworkAnalyzer, "NA": NetworkAnalyzer, "LOAD": ElectronicLoad, "ELOAD": ElectronicLoad, "COUNTER": FrequencyCounter}
                if driver_type == "GENERIC" or (type_map.get(driver_type) and isinstance(dev, type_map.get(driver_type))):
                    return dev
                dev.disconnect()
            except Exception:
                pass
            return None

        # --- Phase 0: Try ONLY Cache (Super Fast) ---
        if cached_resources:
            result = run_probe(cached_resources, "Super Fast (Cache Only)")
            if result:
                return result

        # --- Phase 0.5: Try mDNS (Bonjour) ---
        mdns_resources = _discover_mdns_resources()
        result = run_probe(mdns_resources, "mDNS/Bonjour")
        if result:
            return result

        # --- Phase 1: Try LAN (Quick Search) ---
        result = run_probe(lan_resources, "Fast Track (LAN)")
        if result:
            return result

        # --- Phase 2: Try Full VISA Scan (The 10s Tax) ---
        rm = get_rm()
        visa_resources = list(rm.list_resources())
        result = run_probe(visa_resources, "Slow Track (Full Scan)")
        if result:
            return result
        
        raise ValueError(f"AUTO-Discovery could not find a suitable {driver_type} instrument.")

    # 4. Real Hardware Logic
    idn = ""
    try:
        if "SIM" in resource_address or "MOCK" in resource_address:
            idn = ""
        else:
            base_dev = RealDriver(resource_address, rm=get_rm())
            
            # Smart Probe for Serial Ports (like TDK-Lambda). Runs only on
            # explicit connections -- during AUTO discovery vendor-specific
            # commands must never be sent to arbitrary serial devices (#150).
            if "ASRL" in resource_address and probe_asrl:
                try:
                    base_dev.inst = base_dev.rm.open_resource(resource_address)
                    base_dev.inst.baud_rate = 9600
                    base_dev.inst.read_termination = '\r\n'
                    base_dev.inst.write_termination = '\r\n'
                    base_dev.inst.timeout = 500 # 500ms is enough for local Serial
                    base_dev.inst.write('INST:NSEL 6')
                    time.sleep(0.2)
                    idn = base_dev.inst.query("*IDN?").upper()
                    base_dev.inst.close()
                except Exception:
                    pass
            
            if not idn:
                base_dev.connect()
                # Set a safer timeout for the ID query during discovery
                base_dev.inst.timeout = 2000
                idn = base_dev.get_id().upper()
                base_dev.disconnect()
    except (pyvisa.Error, TimeoutError, ConnectionLost) as e:
        # Expected transport failures (device unreachable, VISA timeout) are
        # logged and degrade to "unidentified". Genuine programming errors are
        # NOT swallowed -- they propagate so regressions surface loudly (#149).
        logger.warning(f"Identification failed for {resource_address}: {e}")
        idn = ""

    # Smart Routing based on IDN
    drv_cls = route_idn(idn)
    final_drv = drv_cls(resource_address) if drv_cls else None

    if not final_drv:
        # No brand matched the IDN. If exactly one driver is registered for the
        # requested type (e.g. a plugin driver with no brand siblings), there's
        # no ambiguity and it's safe to use it. If multiple candidates exist,
        # picking one would be guessing a brand's SCPI dialect for an
        # unidentified instrument, so fall back to the explicit GENERIC driver.
        candidates = [d for d in DriverRegistry.get_drivers_by_type(driver_type) if not d.is_simulated]
        if len(candidates) == 1:
            final_drv = candidates[0](resource_address)
        elif not candidates and driver_type not in KNOWN_DRIVER_TYPES:
            # Issue #146: mirror SIM mode's loud failure. A type that is
            # neither registered nor a canonical category has no driver to
            # fall back to — do NOT silently return GENERIC.
            raise ValueError(
                f"No real driver found for type: {driver_type}"
            )
        else:
            if idn:
                logger.warning(
                    f"Unrecognized instrument IDN '{idn.strip()}' at {resource_address}; "
                    f"using GENERIC driver instead of guessing a {driver_type} brand driver."
                )
            final_drv = GenericDriver(resource_address, rm=get_rm())


    final_drv.connect()
    
    # Update cache with successful manual connection to enable future AUTO discovery
    if resource_address != "AUTO":
        try:
            cache_path = Path(".visa_cache.json")
            cached_resources = []
            if cache_path.exists():
                try:
                    cached_resources = json.loads(cache_path.read_text())
                except (IOError, OSError, json.JSONDecodeError):
                    pass
            new_cache = [resource_address] + [r for r in cached_resources if r != resource_address]
            cache_path.write_text(json.dumps(new_cache[:10]))
        except (IOError, OSError, json.JSONDecodeError):
            pass

    return final_drv

def get_instrument_from_config(config: dict) -> any:
    """Connect to an instrument described by a configuration mapping.

    A thin wrapper over :func:`get_instrument` for config-driven setups such as
    station definitions loaded from disk.

    Parameters
    ----------
    config : dict
        Must contain ``"address"`` -- a VISA resource string or ``"AUTO"`` --
        and ``"type"``, the driver category passed through as ``driver_type``.

    Returns
    -------
    object
        A connected driver instance, as returned by :func:`get_instrument`.

    Raises
    ------
    ValueError
        If either ``"address"`` or ``"type"`` is missing from ``config``.

    Examples
    --------
    >>> get_instrument_from_config({"address": "AUTO", "type": "SCOPE"})
    """
    resource_address = config.get("address")
    driver_type = config.get("type") # Mandatory for test compatibility
    if not resource_address:
        raise ValueError("Missing required configuration key: 'address'")
    if not driver_type:
        raise ValueError("Missing required configuration key: 'type'")
    return get_instrument(resource_address, driver_type)

def load_plugins(plugin_path: str = None):
    """Dynamically loads all available instrument drivers."""
    import importlib
    import pkgutil
    import sys
    
    # 1. Load built-in drivers
    import instrumation.drivers as drivers_pkg
    for _, name, _ in pkgutil.iter_modules(drivers_pkg.__path__):
        importlib.import_module(f"instrumation.drivers.{name}")
            
    # 2. Load from external path if provided
    if plugin_path:
        if plugin_path not in sys.path:
            sys.path.insert(0, plugin_path)
        for _, name, _ in pkgutil.iter_modules([plugin_path]):
            importlib.import_module(name)