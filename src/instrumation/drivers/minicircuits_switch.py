from .base import InstrumentDriver
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("SWITCH")
class MiniCircuitsRCSwitch(RealDriver, InstrumentDriver):
    """Driver for Mini-Circuits RC/RFS Series RF Switch Matrices
    (e.g. RC-4SPDT, RC-1SP4T, RC-2SP4T USB/Ethernet-controlled switches).

    Not a SCPI instrument: uses Mini-Circuits' own flat ASCII command
    set over USB/Ethernet (per the RC/ZTRC Series Programming Manual).
    Each switch is addressed by a letter (A-H) and set to a binary
    state; SPDT switches use 0/1 for the two throws, SPnT switches
    use `SP<n>T:STATE:PORT` to select an active port directly.

    Command Reference (Mini-Circuits RC/ZTRC Series Programming Manual):
        - SET{switch}={0|1}       — sets an individual SPDT switch (A-H)
        - SET{switch}?            — queries an individual switch state
        - SP{n}T:STATE:PORT {port}  — selects the active port on an SPnT switch
        - SP{n}T:STATE:PORT?        — queries the active port
        - GETSWITCH?              — returns a bitmask byte string of all switch states
        - MN?                     — queries model name
        - SN?                     — queries serial number
        - FIRMWARE?               — queries firmware version

    > [!WARNING]
    > This driver could not be verified against Mini-Circuits'
    > official Programming Manual PDF at write time (host was
    > unreachable). Confirmed only via third-party summaries of the
    > `SET[switch]=[state]` command; verify each command against real
    > hardware and prefer `"GENERIC"` passthrough if a command errors.
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
        """No-op: the Mini-Circuits switch protocol has no SCPI error queue."""
        pass

    def safe_send(self, command: str) -> None:
        self.write(command)

    def query_ascii(self, command: str) -> str:
        return self.query(command)

    def get_id(self) -> str:
        return self.query("MN?")

    def set_switch(self, switch: str, state: bool) -> None:
        """Sets a single SPDT switch (A-H) to state 0 or 1."""
        self.write(f"SET{switch.upper()}={'1' if state else '0'}")

    def get_switch(self, switch: str) -> bool:
        """Queries a single SPDT switch (A-H) state."""
        resp = self.query(f"SET{switch.upper()}?")
        return resp.strip() in ("1", "ON")

    def set_port(self, switch_number: int, throws: int, port: int) -> None:
        """Selects the active port on an SPnT switch, e.g. set_port(1, 4, 3)
        selects port 3 on switch 1's SP4T."""
        self.write(f"SP{throws}T:STATE:PORT {port}")

    def get_port(self, throws: int) -> int:
        """Queries the active port on an SPnT switch."""
        return int(self.query(f"SP{throws}T:STATE:PORT?"))

    def get_all_switches_bitmask(self) -> int:
        """Returns the raw bitmask byte of all switch states (GETSWITCH?)."""
        return int(self.query("GETSWITCH?"))

    def get_serial_number(self) -> str:
        return self.query("SN?")

    def get_firmware_version(self) -> str:
        return self.query("FIRMWARE?")

    def measure_frequency(self) -> MeasurementResult:
        return MeasurementResult(0.0, "Hz")

    def measure_duty_cycle(self) -> MeasurementResult:
        return MeasurementResult(0.0, "%")

    def measure_v_peak_to_peak(self) -> MeasurementResult:
        return MeasurementResult(0.0, "V")

    def shutdown_safety(self) -> None:
        pass
