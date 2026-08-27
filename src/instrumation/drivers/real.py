import pyvisa
import re
import time
from typing import List, Tuple
from .base import InstrumentDriver
from ..results import MeasurementResult
from ..exceptions import ConnectionLost, ConfigurationError, InstrumentTimeout

# Marker for real SCPI SYST:ERR responses: [+-]<code>,"<msg>"
_SCPI_ERROR_RE = re.compile(r'^[+-]?\d+,"')

class RealDriver(InstrumentDriver):
    """Refined RealDriver with Auto-Handshake Engine."""
    @staticmethod
    def scan() -> Tuple[str, ...]:
        """Scans for available instruments."""
        from ..factory import get_rm
        return get_rm().list_resources()

    def __init__(self, resource: str, rm: pyvisa.ResourceManager = None) -> None:
        super().__init__(resource)
        from ..factory import get_rm
        if rm:
            self.rm = rm
        else:
            try:
                self.rm = get_rm()
            except Exception:
                self.rm = None
        self.inst = None
        self.is_simulated = False
        self.bridge_config: dict = {} # e.g. {"type": "prologix", "gpib_address": 1}
        # Dependency-injection knob: test doubles that don't model the SCPI
        # error queue disable error-checking explicitly (never via class-name
        # sniffing of the instrument session).
        self.check_errors_enabled = True

    def connect(self) -> None:
        """Connects, runs sync_config, and discovers identity/options."""
        try:
            self.inst = self.rm.open_resource(self.resource)
            self.inst.timeout = 5000
            self.connected = True
            
            # Sync & Discovery
            self.sync_config()
            self._discover_identity()
            self._discover_options()
        except pyvisa.VisaIOError as e:
            raise ConnectionLost(f"Failed to connect to {self.resource}: {e}")

    def _discover_identity(self) -> None:
        idn = self.query("*IDN?").split(',')
        if len(idn) >= 4:
            self.identity = {
                "manufacturer": idn[0].strip(),
                "model": idn[1].strip(),
                "serial": idn[2].strip(),
                "version": idn[3].strip()
            }

    def _discover_options(self) -> None:
        try:
            self.options = self.query("*OPT?").split(',')
        except Exception:
            self.options = []

    def disconnect(self) -> None:
        if self.inst:
            self.inst.close()
        self.connected = False

    def write(self, command: str) -> None:
        if not self.inst:
            raise ConnectionLost("Not connected.")
        
        # Bridge handling
        if self.bridge_config.get("type") == "prologix":
            if not command.endswith("\n") and not command.startswith("++"):
                command += "\n"
        
        self.inst.write(command)

    def safe_send(self, command: str) -> None:
        """Sends command and automatically runs SYST:ERR?."""
        self.write(command)
        self.check_errors()

    def query(self, command: str) -> str:
        if not self.inst:
            raise ConnectionLost("Not connected.")
        
        # Bridge handling
        if self.bridge_config.get("type") == "prologix":
            self.write(command)
            self.write("++read eoi")
            return self.inst.read().strip()
            
        return self.inst.query(command).strip()

    def query_ascii(self, command: str) -> str:
        """Sends command, reads response, and checks for errors."""
        resp = self.query(command)
        self.check_errors()
        return resp

    def query_binary_values(self, command: str, datatype: str = 'f', is_big_endian: bool = False) -> List[float]:
        if not self.inst:
            raise ConnectionLost("Not connected.")
        return self.inst.query_binary_values(command, datatype=datatype, is_big_endian=is_big_endian)

    # --- Global Logic & Sync ---
    def clear_status(self) -> None:
        self.write("*CLS")

    def sync_config(self) -> None:
        """Ensures device isn't busy with previous tasks."""
        self.write("*CLS")
        self.write("*WAI")

    def wait_ready(self, timeout: float = 30.0) -> None:
        """Deterministic polling for *OPC?."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Direct query to PyVISA to avoid recursion
                if self.inst.query("*OPC?").strip() == "1":
                    return
            except Exception:
                pass
            time.sleep(0.1)
        raise InstrumentTimeout(f"Timeout waiting for *OPC? on {self.resource}")

    def check_errors(self) -> None:
        """Queries SYST:ERR? and updates local error_stack."""
        if not self.check_errors_enabled:
            return
        err = self.inst.query("SYST:ERR?").strip()
        if not isinstance(err, str):
            return  # mock children / non-SCPI responses are not error-queue output
        # Only genuine SCPI error-queue responses (e.g. '-221,"Settings conflict"')
        # trigger a hardware error. Measurement values or mock children are not
        # error-queue output and must not raise.
        if _SCPI_ERROR_RE.match(err) and '+0,"No error"' not in err and '0,"No error"' not in err:
            self.error_stack.append(err)
            resource_name = self.identity.get("model") or self.resource
            raise ConfigurationError(f"Hardware Error on {resource_name}: {err}")

    def get_id(self) -> str:
        return self.query("*IDN?")

    def preset(self, automation_optimized: bool = True) -> None:
        self.write("*RST")
        self.sync_config()

    def shutdown_safety(self) -> None:
        """Default safety: Clear and Wait."""
        self.sync_config()
        
    def measure_frequency(self) -> MeasurementResult: return MeasurementResult(0.0, "Hz")
    def measure_duty_cycle(self) -> MeasurementResult: return MeasurementResult(0.0, "%")
    def measure_v_peak_to_peak(self) -> MeasurementResult: return MeasurementResult(0.0, "V")
