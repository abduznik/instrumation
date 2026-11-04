from .base import InstrumentDriver
from .registry import register_driver
from .real import RealDriver


@register_driver("SWITCH")
class MiniCircuitsRCSwitch(RealDriver, InstrumentDriver):
    """Driver for Mini-Circuits RC/ZTRC Series RF switch matrices
    (RC-1SPDT-A18 ... RC-8SPDT-A18, RC-1SP4T-A26, RC-2SP4T-A26,
    RC-2SP6T-A18, RC-2MTS-18, ZTRC-xSPDT-A18).

    Not a SCPI instrument: uses Mini-Circuits' flat ASCII command set over
    USB HID or Ethernet (Telnet/HTTP), per the "Mechanical Switch Systems"
    Programming Manual, Rev. B7 (7-Jun-24).

    Command Reference (manual section 3):
        - SET{switch}={0|1}        — set one SPDT/transfer switch (A-H);
                                     0 = COM->port 1, 1 = COM->port 2
        - SETP={states}            — set all SPDT/transfer switches (bitmask,
                                     LSB = switch A) or all SP4T/SP6T ports
        - SWPORT?                  — read all switch states as a bitmask
                                     (LSB = switch A, MSB = switch H)
        - SP4T{s}:STATE:{port}     — select a port on SP4T switch s (A/B);
                                     0 = all ports disconnected
        - SP6T{s}:STATE:{port}     — same for SP6T switch s (ports 0-6)
        - SP4T{s}:STATE?           — current port of that SP4T/SP6T switch
        - MN? / SN? / FIRMWARE?    — model ("MN=..."), serial ("SN=..."), firmware
        - TEMP{n}? / HEATALARM? / FAN? — temperature, over-temperature alarm, fan

    This command set defines no per-switch query and no `*IDN?`, `*OPT?`,
    `*RST`, `*CLS` or error queue: single-switch state is read out of the
    `SWPORT?` bitmask, and identity comes from `MN?`/`SN?`/`FIRMWARE?`.
    """

    def preset(self, automation_optimized: bool = True) -> None:
        pass

    def clear_status(self) -> None:
        pass

    def sync_config(self) -> None:
        pass

    def wait_ready(self, timeout: float = 30.0) -> None:
        pass

    def check_errors(self) -> None:
        """No-op: this command set has no SCPI error queue; a setter answers
        0 (failed) or 1 (ok) directly."""
        pass

    def safe_send(self, command: str) -> None:
        self.write(command)

    def query_ascii(self, command: str) -> str:
        return self.query(command)

    @staticmethod
    def _strip(value: str) -> str:
        """Drop the `MN=`/`SN=`-style key the manual puts in front of a reply."""
        return value.strip().split("=", 1)[-1].strip()

    def get_id(self) -> str:
        return self._strip(self.query("MN?"))

    def get_serial_number(self) -> str:
        return self._strip(self.query("SN?"))

    def get_firmware_version(self) -> str:
        return self.query("FIRMWARE?").strip()

    def _discover_identity(self) -> None:
        """No *IDN? on this instrument -- build identity from MN?/SN?/FIRMWARE?."""
        self.identity["manufacturer"] = "Mini-Circuits"
        for key, query in (("model", "MN?"), ("serial", "SN?"), ("version", "FIRMWARE?")):
            try:
                self.identity[key] = self._strip(self.query(query))
            except Exception:
                pass  # identity is cosmetic; a missing reply must not fail connect()

    def _discover_options(self) -> None:
        """No *OPT? on this instrument: the feature set is fixed per model."""
        self.options = []

    def set_switch(self, switch: str, state: bool) -> None:
        """Sets a single SPDT/transfer switch (A-H) to state 0 or 1."""
        self.write(f"SET{switch.upper()}={'1' if state else '0'}")

    def get_switch(self, switch: str) -> bool:
        """Reads a single SPDT/transfer switch (A-H) out of the SWPORT? bitmask.

        The manual defines no per-switch query, so this costs one SWPORT? read.
        """
        index = ord(switch.upper()) - ord("A")
        if not 0 <= index <= 7:
            raise ValueError(f"switch must be A-H, got {switch!r}")
        return bool((self.get_all_switches_bitmask() >> index) & 1)

    def get_all_switches_bitmask(self) -> int:
        """Returns the SWPORT? bitmask of all switch states (bit 0 = switch A)."""
        return int(self.query("SWPORT?").strip() or 0)

    def set_port(self, switch: str, throws: int, port: int) -> None:
        """Selects the active port on an SPnT switch, e.g. set_port("a", 4, 3)
        connects COM to port 3 on SP4T switch A. Port 0 disconnects all ports."""
        if throws not in (4, 6):
            raise ValueError(f"throws must be 4 or 6, got {throws}")
        if not 0 <= port <= throws:
            raise ValueError(f"port must be 0-{throws}, got {port}")
        self.write(f"SP{throws}T{switch.upper()}:STATE:{port}")

    def get_port(self, switch: str, throws: int) -> int:
        """Queries the active port of an SPnT switch (A/B): 0 = disconnected."""
        if throws not in (4, 6):
            raise ValueError(f"throws must be 4 or 6, got {throws}")
        return int(self.query(f"SP{throws}T{switch.upper()}:STATE?").strip() or 0)

    def shutdown_safety(self) -> None:
        pass
