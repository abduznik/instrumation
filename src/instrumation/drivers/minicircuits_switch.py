from .base import InstrumentDriver
from .registry import register_driver
from .real import RealDriver


@register_driver("SWITCH")
class MiniCircuitsRCSwitch(RealDriver, InstrumentDriver):
    """Driver for Mini-Circuits RC/RFS Series RF Switch Matrices
    (e.g. RC-4SPDT, RC-1SP4T, RC-2SP4T USB/Ethernet-controlled switches).

    Not a SCPI instrument: uses Mini-Circuits' own flat ASCII command
    set over USB/Ethernet (per the RC/ZTRC Series Programming Manual).
    Each SPDT switch is addressed by a letter (A-H) and set to a binary
    state; SPDT switches use 0/1 for the two throws, SPnT switches use
    `SP<n>T<switch>:STATE:<port>` to select an active port directly.

    Command Reference (Mechanical Switch Systems — Programming Manual,
    Rev. B7, 7-Jun-24):
        - SET{switch}={0|1}           — sets an individual SPDT switch (A-H)
        - SP{n}T{switch}:STATE:{port} — sets an individual SPnT switch (A/B; e.g. SP4TA:STATE:3)
        - SP{n}T{switch}:STATE?       — queries the state of a single SPnT switch (e.g. SP4TA:STATE?)
        - SETP={states}               — sets all SPnT switches at once (write-only)
        - SWPORT?                     — returns a bitmask of all switch states (LSB = switch A)
        - MN?                         — queries model name (replies `MN=<model>`)
        - SN?                         — queries serial number (replies `SN=<serial>`)
        - FIRMWARE?                   — queries firmware version

    There is no per-switch state query (`SET{switch}?` does not exist);
    per-switch SPDT state is derived from the `SWPORT?` bitmask.

    Command syntax verified against the Mini-Circuits Mechanical Switch
    Systems Programming Manual Rev. B7 (7-Jun-24). Not yet verified
    against physical hardware.
    """

    def preset(self, automation_optimized: bool = True) -> None:
        pass

    def clear_status(self) -> None:
        pass

    def sync_config(self) -> None:
        """No-op: the manual defines no *CLS/*WAI (or any standard SCPI
        synchronisation commands); sending them leaves unread responses
        in the receive buffer."""
        pass

    def wait_ready(self, timeout: float = 30.0) -> None:
        pass

    def check_errors(self) -> None:
        """No-op: the Mini-Circuits switch protocol has no SCPI error queue."""
        pass

    def safe_send(self, command: str) -> None:
        self.write(command)

    def query_ascii(self, command: str) -> str:
        return self.query(command)

    @staticmethod
    def _strip_prefix(response: str, prefix: str) -> str:
        resp = response.strip()
        if resp.upper().startswith(prefix.upper()):
            resp = resp[len(prefix):]
        return resp.strip()

    def get_id(self) -> str:
        return self._strip_prefix(self.query("MN?"), "MN=")

    def _discover_identity(self) -> None:
        # No *IDN? on this protocol; identification is MN?/SN?/FIRMWARE?.
        self.identity = {
            "manufacturer": "Mini-Circuits",
            "model": self._strip_prefix(self.query("MN?"), "MN="),
            "serial": self._strip_prefix(self.query("SN?"), "SN="),
            "version": self.query("FIRMWARE?").strip(),
        }

    def _discover_options(self) -> None:
        """No *OPT? query on this protocol -- feature set is fixed, no options."""
        self.options = []

    def set_switch(self, switch: str, state: bool) -> None:
        """Sets a single SPDT switch (A-H) to state 0 or 1."""
        self.write(f"SET{switch.upper()}={'1' if state else '0'}")

    def get_switch(self, switch: str) -> bool:
        """Queries a single SPDT switch (A-H) state via the SWPORT? bitmask
        (LSB = switch A)."""
        index = ord(switch.upper()) - ord('A')
        return bool((self.get_all_switches_bitmask() >> index) & 1)

    def set_port(self, switch: str, throws: int, port: int) -> None:
        """Selects the active port on an SPnT switch, e.g. set_port("A", 4, 3)
        selects port 3 on switch A of an SP4T (`SP4TA:STATE:3`)."""
        self.write(f"SP{throws}T{switch.upper()}:STATE:{port}")

    def get_port(self, switch: str, throws: int) -> int:
        """Queries the active port on an SPnT switch (e.g. `SP4TA:STATE?`)."""
        return int(self.query(f"SP{throws}T{switch.upper()}:STATE?"))

    def get_all_switches_bitmask(self) -> int:
        """Returns the raw bitmask byte of all switch states (SWPORT?)."""
        return int(self.query("SWPORT?"))

    def get_serial_number(self) -> str:
        return self._strip_prefix(self.query("SN?"), "SN=")

    def get_firmware_version(self) -> str:
        return self.query("FIRMWARE?").strip()

    def shutdown_safety(self) -> None:
        pass
