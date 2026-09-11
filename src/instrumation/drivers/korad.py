from .base import PowerSupply
from .registry import register_driver
from .real import RealDriver
from ..exceptions import ConnectionLost
from ..results import MeasurementResult


@register_driver("PSU")
class KoradKA3005P(RealDriver, PowerSupply):
    """Driver for Korad KA3005P Single-Output Programmable DC Power Supply.

    Validated Model: KA3005P. This is NOT a SCPI instrument: it speaks
    Korad's own flat ASCII command set over serial (9600 8N1, no line
    termination, no error queue, no ``*RST``/``*CLS``/``*OPC?``). This
    driver overrides the ``RealDriver`` SCPI assumptions accordingly --
    ``check_errors``, ``sync_config`` and ``clear_status`` are no-ops,
    and ``safe_send``/``query_ascii`` skip the ``SYST:ERR?`` round-trip
    entirely. Widely cloned by Tenma, RS, Velleman, and Stamos under
    different model numbers with an identical command set.

    Protocol Reference (Korad KA3005P serial protocol, per sigrok.org):
        - *IDN?                    — returns e.g. "KORADKA3005PV2.0"
        - STATUS?                  — single status byte (bit0=CC/CV,
                                      bit5=OCP tripped, bit6=output on)
        - VSET1:<v> / VSET1?       — set/query voltage setpoint
        - ISET1:<i> / ISET1?       — set/query current limit setpoint
        - VOUT1? / IOUT1?          — measured actual voltage/current
        - OUT1 / OUT0              — output on/off
        - OVP1 / OVP0              — enable/disable over-voltage protection
        - OCP1 / OCP0              — enable/disable over-current protection
        - TRACK0/1/2               — 0=independent, 1=series, 2=parallel
        - SAV1-5 / RCL1-5          — save/recall memory slot
    """

    def connect(self) -> None:
        try:
            self.inst = self.rm.open_resource(self.resource)
            self.inst.baud_rate = 9600
            self.inst.data_bits = 8
            self.inst.write_termination = ''
            self.inst.read_termination = ''
            self.inst.timeout = 3000
            self.connected = True
            self._discover_identity()
        except Exception as e:
            self.connected = False
            raise ConnectionLost(f"Failed to connect to Korad KA3005P at {self.resource}: {e}")

    def _discover_identity(self) -> None:
        idn = self.query("*IDN?").strip()
        self.identity = {"manufacturer": "Korad", "model": idn, "serial": "", "version": ""}

    def get_id(self) -> str:
        return self.query("*IDN?")

    def clear_status(self) -> None:
        pass

    def sync_config(self) -> None:
        pass

    def wait_ready(self, timeout: float = 30.0) -> None:
        pass

    def check_errors(self) -> None:
        """No-op: the Korad protocol has no SCPI error queue."""
        pass

    def safe_send(self, command: str) -> None:
        self.write(command)

    def query_ascii(self, command: str) -> str:
        return self.query(command)

    def preset(self, automation_optimized: bool = True) -> None:
        """Korad has no *RST; presets to output off, 0V, minimum current limit."""
        self.set_output(False)
        self.set_voltage(0.0)
        self.set_current_limit(0.0)

    def set_voltage(self, voltage: float) -> None:
        self.write(f"VSET1:{voltage:.2f}")

    def get_voltage(self) -> float:
        """Returns the programmed voltage setpoint."""
        return float(self.query("VSET1?"))

    def set_current_limit(self, current: float) -> None:
        self.write(f"ISET1:{current:.3f}")

    def get_current(self) -> MeasurementResult:
        """Returns the programmed current limit setpoint."""
        val = self.query("ISET1?")
        return MeasurementResult(float(val), "A")

    def set_output(self, state: bool) -> None:
        self.write("OUT1" if state else "OUT0")

    def get_output(self) -> bool:
        status = self.query("STATUS?")
        if not status:
            return False
        return bool(ord(status[0]) & 0x40)

    def set_ovp(self, voltage: float) -> None:
        """Sets voltage setpoint and enables OVP (KA3005P has no separate OVP trip level)."""
        self.set_voltage(voltage)
        self.write("OVP1")

    def set_ocp(self, current: float) -> None:
        """Sets current setpoint and enables OCP (KA3005P has no separate OCP trip level)."""
        self.set_current_limit(current)
        self.write("OCP1")

    def clear_protection(self) -> None:
        self.write("OVP0")
        self.write("OCP0")

    def measure_voltage_actual(self) -> MeasurementResult:
        val = self.query("VOUT1?")
        return MeasurementResult(float(val), "V")

    def measure_current(self) -> MeasurementResult:
        val = self.query("IOUT1?")
        return MeasurementResult(float(val), "A")

    def set_track_mode(self, mode: int) -> None:
        """Sets channel tracking: 0=independent, 1=series, 2=parallel."""
        if mode not in (0, 1, 2):
            raise ValueError("mode must be 0 (independent), 1 (series), or 2 (parallel)")
        self.write(f"TRACK{mode}")

    def save_state(self, index: int) -> None:
        if not (1 <= index <= 5):
            raise ValueError("Index must be 1-5")
        self.write(f"SAV{index}")

    def load_state(self, index: int) -> None:
        if not (1 <= index <= 5):
            raise ValueError("Index must be 1-5")
        self.write(f"RCL{index}")

    def measure_frequency(self) -> MeasurementResult:
        return MeasurementResult(0.0, "Hz")

    def measure_duty_cycle(self) -> MeasurementResult:
        return MeasurementResult(0.0, "%")

    def measure_v_peak_to_peak(self) -> MeasurementResult:
        return MeasurementResult(0.0, "V")

    def shutdown_safety(self) -> None:
        self.set_output(False)
        self.set_voltage(0.0)
