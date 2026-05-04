import time
from .base import PowerSupply
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult
from ..exceptions import InstrumentError

@register_driver("PSU")
class TDKLambdaZPlus(RealDriver, PowerSupply):
    """Driver for TDK-Lambda Z+ Series Power Supplies."""

    def connect(self):
        """Overrides connect to send INST:NSEL command before identity check."""
        try:
            # 1. Establish raw connection
            self.inst = self.rm.open_resource(self.resource)
            self.inst.baud_rate = 9600
            self.inst.read_termination = '\r\n'
            self.inst.write_termination = '\r\n'
            self.inst.timeout = 5000 
            self.connected = True
            
            # 2. Wake up the unit (NSEL 6 is the SCPI way for Z+)
            self.inst.write('INST:NSEL 6')
            time.sleep(1.0) # Buffer for PSU internal controller
            
            # 3. Now run the standard discovery
            self._discover_identity()
            self._discover_options()
            self._discover_capabilities()
        except Exception as e:
            self.connected = False
            raise InstrumentError(f"Failed to connect to TDK-Lambda at {self.resource}: {e}")

    def _discover_capabilities(self):
        """Query the Z+ for its actual voltage and current limits."""
        try:
            self.max_voltage = float(self.query(":VOLT? MAX"))
            self.max_power_dbm = 0.0 # Not a signal generator
            # We don't have a max_current in the base class, but we can store it
            self.max_current = float(self.query(":CURR? MAX"))
        except Exception:
            pass


    def preset(self, automation_optimized: bool = True):
        self.write("*RST")
        self.sync_config()

    def set_voltage(self, voltage: float):
        self.safe_send(f":VOLT {voltage}")

    def get_voltage(self) -> float:
        """Returns the programmed voltage setpoint."""
        return float(self.query_ascii(":VOLT?"))

    def get_current(self) -> float:
        """Returns the programmed current setpoint (CC limit)."""
        return float(self.query_ascii(":CURR?"))

    def get_current_limit(self) -> float:
        """Alias for get_current."""
        return self.get_current()

    def measure_current(self) -> MeasurementResult:
        """Queries the actual measured output current."""
        val = self.query_ascii(":MEAS:CURR?")
        return MeasurementResult(float(val), "A")

    def set_output(self, state: bool):
        self.write(f":OUTP {'ON' if state else 'OFF'}")

    def get_output(self) -> bool:
        state = self.query_ascii(":OUTP?")
        return state == "1" or state.upper() == "ON"

    def set_ovp(self, voltage: float):
        self.write(f":VOLT:PROT {voltage}")

    def get_ovp(self) -> float:
        return float(self.query(":VOLT:PROT?"))

    def set_current(self, current: float):
        """Sets the current setpoint (CC limit)."""
        self.write(f":CURR {current}")

    def set_current_limit(self, current: float):
        """Alias for set_current."""
        self.set_current(current)

    def set_ocp(self, current: float):
        """Sets the Over-Current Protection trip point."""
        self.write(f":CURR:PROT {current}")

    def get_ocp(self) -> float:
        return float(self.query(":CURR:PROT?"))

    def clear_protection(self):
        """Clears hardware protection latches (OVP/OCP)."""
        self.write(":OUTP:PROT:CLE")

    def measure_voltage(self) -> MeasurementResult:
        """Alias for measure_voltage_actual."""
        return self.measure_voltage_actual()

    def measure_voltage_actual(self) -> MeasurementResult:
        """Queries the actual measured output voltage."""
        val = self.query_ascii(":MEAS:VOLT?")
        return MeasurementResult(float(val), "V")

    def measure_power(self) -> MeasurementResult:
        """Queries the actual measured output power (Watts)."""
        val = self.query_ascii(":MEAS:POW?")
        return MeasurementResult(float(val), "W")

    def set_foldback_mode(self, mode: str):
        """Sets the foldback protection mode (OFF, CC, or CV)."""
        mode = mode.upper()
        if mode not in ["OFF", "CC", "CV"]:
            raise ValueError("Foldback mode must be OFF, CC, or CV")
        self.write(f":OUTP:PROT:FOLD {mode}")

    def set_foldback_delay(self, seconds: float):
        """Sets the delay for foldback protection (0-100 seconds)."""
        self.write(f":OUTP:PROT:DEL {seconds}")

    def set_autostart(self, state: bool):
        """Sets the Power-ON state (SAFE/OFF or AUTO/ON)."""
        self.write(f":OUTP:PON {'ON' if state else 'OFF'}")

    def get_mode(self) -> str:
        """Returns the current operation mode (CV, CC, or OFF)."""
        return self.query_ascii(":OUTP:MODE?").strip()

    def set_remote_state(self, state: str):
        """Sets the remote state (LOC, REM, or LLO)."""
        state = state.upper()
        if state not in ["LOC", "REM", "LLO"]:
            raise ValueError("State must be LOC, REM, or LLO")
        self.write(f":SYST:REM {state}")

    def save_state(self, index: int):
        """Saves current state to memory (1-4)."""
        if not (1 <= index <= 4):
            raise ValueError("Index must be 1-4")
        self.write(f"*SAV {index}")

    def load_state(self, index: int):
        """Recalls state from memory (1-4)."""
        if not (1 <= index <= 4):
            raise ValueError("Index must be 1-4")
        self.write(f"*RCL {index}")

    def measure_frequency(self) -> MeasurementResult: return MeasurementResult(0.0, "Hz")
    def measure_duty_cycle(self) -> MeasurementResult: return MeasurementResult(0.0, "%")
    def measure_v_peak_to_peak(self) -> MeasurementResult: return MeasurementResult(0.0, "V")

    def shutdown_safety(self):
        """Safety first: Disable output and zero voltage."""
        self.set_output(False)
        self.set_voltage(0.0)
        self.sync_config()
