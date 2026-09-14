from .base import PowerSupply
from .registry import register_driver
from .real import RealDriver
from ..exceptions import ConnectionLost
from ..results import MeasurementResult


@register_driver("PSU")
class BKPrecision1685B(RealDriver, PowerSupply):
    """Driver for BK Precision 1685B/1687B/1688B Switching DC Power Supplies.

    Validated Model: 1685B (single output). This is NOT a SCPI-99
    instrument: like `KoradKA3005P`, it speaks BK Precision's own flat
    ASCII command set over a USB virtual COM port -- distinct from the
    multi-channel SCPI-based `BKPrecision9130B` driver already in this
    library, which targets a different BK Precision product line.

    Command Reference (1685B/1687B/1688B Series Programming Manual):
        - *IDN?                     — identification string
        - VSET1:<v> / VSET1?        — set/query voltage setpoint
        - ISET1:<i> / ISET1?        — set/query current limit setpoint
        - VOUT1? / IOUT1?           — measured actual voltage/current
        - OUT1 / OUT0               — output on/off
        - OUT?                      — query output state (0/1)
        - OVP1:<v> / OVP0           — set OVP trip point / disable OVP
        - OCP1:<i> / OCP0           — set OCP trip point / disable OCP
    """

    def connect(self) -> None:
        try:
            self.inst = self.rm.open_resource(self.resource)
            self.inst.baud_rate = 9600
            self.inst.timeout = 3000
            self.connected = True
            self._discover_identity()
        except Exception as e:
            self.connected = False
            raise ConnectionLost(f"Failed to connect to BK Precision 1685B at {self.resource}: {e}")

    def _discover_identity(self) -> None:
        idn = self.query("*IDN?").strip()
        self.identity = {"manufacturer": "BK Precision", "model": idn, "serial": "", "version": ""}

    def get_id(self) -> str:
        return self.query("*IDN?")

    def clear_status(self) -> None:
        pass

    def sync_config(self) -> None:
        pass

    def wait_ready(self, timeout: float = 30.0) -> None:
        pass

    def check_errors(self) -> None:
        """No-op: the 1685B protocol has no SCPI error queue."""
        pass

    def safe_send(self, command: str) -> None:
        self.write(command)

    def query_ascii(self, command: str) -> str:
        return self.query(command)

    def preset(self, automation_optimized: bool = True) -> None:
        """No *RST on this protocol; presets to output off, 0V, minimum current limit."""
        self.set_output(False)
        self.set_voltage(0.0)
        self.set_current_limit(0.0)

    def set_voltage(self, voltage: float) -> None:
        self.write(f"VSET1:{voltage:.2f}")

    def get_voltage(self) -> float:
        return float(self.query("VSET1?"))

    def set_current_limit(self, current: float) -> None:
        self.write(f"ISET1:{current:.3f}")

    def get_current(self) -> MeasurementResult:
        val = self.query("ISET1?")
        return MeasurementResult(float(val), "A")

    def set_output(self, state: bool) -> None:
        self.write("OUT1" if state else "OUT0")

    def get_output(self) -> bool:
        return self.query("OUT?").strip() in ("1", "ON")

    def set_ovp(self, voltage: float) -> None:
        self.write(f"OVP1:{voltage:.2f}")

    def set_ocp(self, current: float) -> None:
        self.write(f"OCP1:{current:.3f}")

    def clear_protection(self) -> None:
        self.write("OVP0")
        self.write("OCP0")

    def measure_voltage_actual(self) -> MeasurementResult:
        val = self.query("VOUT1?")
        return MeasurementResult(float(val), "V")

    def measure_current(self) -> MeasurementResult:
        val = self.query("IOUT1?")
        return MeasurementResult(float(val), "A")

    def shutdown_safety(self) -> None:
        self.set_output(False)
        self.set_voltage(0.0)
