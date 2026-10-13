from .base import PowerSupply
from .registry import register_driver
from .real import RealDriver
from ..exceptions import ConnectionLost
from ..results import MeasurementResult

# The 1685B terminates every command/reply with a bare CR (0x0D); the manual
# explicitly says "do not append line feeds". chr(13) avoids embedding a
# literal escape in the source.
_CR = chr(13)

# GMAX max-rating (volts, amps) -> model number. GMAX is the only
# identifying readback: the 1685B protocol has no *IDN?.
_GMAX_TO_MODEL = {
    (60.0, 5.0): "1685B",
    (36.0, 10.0): "1687B",
    (18.0, 20.0): "1688B",
}


@register_driver("PSU")
class BKPrecision1685B(RealDriver, PowerSupply):
    """Driver for BK Precision 1685B/1687B/1688B Switching DC Power Supplies.

    Validated Model: 1685B (single output). This is NOT a SCPI-99
    instrument: it speaks BK Precision's own flat ASCII command set over a
    USB virtual COM port (9600 8N1, CR-terminated, no line feed). Like
    `KoradKA3005P` there is no SCPI error queue and no IEEE-488.2 common
    commands -- ``check_errors``/``sync_config``/``clear_status``/
    ``wait_ready`` are no-ops. Distinct from the SCPI-based
    `BKPrecision9130B` driver (a different product line).

    Command Reference (1685B/1687B/1688B Programming Manual, Command Set):
        - VOLT<vvv>              -- set voltage setpoint (3 digits, x10;
                                    VOLT010 = 1.0 V)
        - CURR<iii>              -- set current-limit setpoint (x10;
                                    CURR025 = 2.5 A)
        - GETS                   -- query setpoints; returns ``<vvv><iii>``
                                    (voltage x10, current x10)
        - GETD                   -- query display readings; returns
                                    ``<vvvv><iiii><s>`` (voltage x100,
                                    current x100, status 0=CV / 1=CC)
        - SOUT<0|1>              -- output control; **0 = ON, 1 = OFF**
                                    (inverted polarity)
        - SOVP<vvv>              -- set upper voltage limit (OVP, x10)
        - SOCP<iii>              -- set upper current limit (OCP, x10)
        - GOVP                   -- query upper voltage limit (x10)
        - GOCP                   -- query upper current limit (x10)
        - GMAX                   -- query supply max V and I (x10 each);
                                    the only model-identifying readback
                                    (there is no *IDN?)

    There is no output-state readback (no ``OUT?``), no protection-clear
    command (no ``OVP0``/``OCP0``), and no ``*IDN?``.
    """

    def connect(self) -> None:
        try:
            self.inst = self.rm.open_resource(self.resource)
            self.inst.baud_rate = 9600
            self.inst.data_bits = 8
            self.inst.write_termination = _CR
            self.inst.read_termination = _CR
            self.inst.timeout = 3000
            self._last_output = False
            self.connected = True
            self._discover_identity()
        except Exception as e:
            self.connected = False
            raise ConnectionLost(f"Failed to connect to BK Precision 1685B at {self.resource}: {e}")

    def _query_value(self, command: str) -> str:
        """Query, then return the data line (drops the trailing OK ack)."""
        raw = self.query(command)
        for line in raw.replace(_CR, "\n").split("\n"):
            line = line.strip()
            if line and line.upper() != "OK":
                return line
        return ""

    @staticmethod
    def _enc3(value: float) -> str:
        """Fixed-point 3-digit x10 encoding (1.0 V -> ``010``)."""
        return f"{round(value * 10):03d}"

    def _discover_identity(self) -> None:
        # No *IDN? on this protocol; infer the model from GMAX max ratings.
        # Defensive: a non-numeric / short GMAX reply must not brick connect().
        model = "168xB"
        try:
            gmax = self._query_value("GMAX")
            if len(gmax) >= 6:
                vmax = int(gmax[:3]) / 10.0
                amax = int(gmax[3:6]) / 10.0
                model = _GMAX_TO_MODEL.get((round(vmax, 1), round(amax, 1)), "168xB")
        except (ValueError, IndexError):
            pass
        self.identity = {"manufacturer": "BK Precision", "model": model, "serial": "", "version": ""}

    def get_id(self) -> str:
        # No *IDN?; return a constructed identity from the GMAX-inferred model.
        return f"BK PRECISION,{self.identity.get('model', '168xB')}"

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
        """No *RST on this protocol; presets to output off, 0V, 0A limit."""
        self.set_output(False)
        self.set_voltage(0.0)
        self.set_current_limit(0.0)

    def set_voltage(self, voltage: float) -> None:
        self.write(f"VOLT{self._enc3(voltage)}")

    def get_voltage(self) -> float:
        return float(self._query_value("GETS")[:3]) / 10.0

    def set_current_limit(self, current: float) -> None:
        self.write(f"CURR{self._enc3(current)}")

    def get_current(self) -> MeasurementResult:
        return MeasurementResult(float(self._query_value("GETS")[3:6]) / 10.0, "A")

    def set_output(self, state: bool) -> None:
        # Manual: SOUT 0 = ON, 1 = OFF (inverted polarity).
        self.write("SOUT0" if state else "SOUT1")
        self._last_output = state

    def get_output(self) -> bool:
        # No output-state readback on this protocol; return last commanded state.
        return self._last_output

    def set_ovp(self, voltage: float) -> None:
        self.write(f"SOVP{self._enc3(voltage)}")

    def set_ocp(self, current: float) -> None:
        self.write(f"SOCP{self._enc3(current)}")

    def measure_voltage_actual(self) -> MeasurementResult:
        return MeasurementResult(float(self._query_value("GETD")[:4]) / 100.0, "V")

    def measure_current(self) -> MeasurementResult:
        return MeasurementResult(float(self._query_value("GETD")[4:8]) / 100.0, "A")

    def shutdown_safety(self) -> None:
        self.set_output(False)
        self.set_voltage(0.0)
