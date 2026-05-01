import pyvisa
from .base import InstrumentDriver, Multimeter
from ..results import MeasurementResult
from ..exceptions import ConnectionLost, InstrumentTimeout, InstrumentError

class RealDriver(InstrumentDriver):
    """
    Generic Driver for physical hardware.
    """
    def __init__(self, resource):
        super().__init__(resource)
        self.rm = pyvisa.ResourceManager()
        self.inst = None

    def connect(self):
        try:
            self.inst = self.rm.open_resource(self.resource)
            self.inst.timeout = 5000
            self.connected = True
            print(f"Connected to {self.resource}")
        except Exception as e:
            raise ConnectionLost(f"Failed to connect to {self.resource}: {e}")

    def disconnect(self):
        if self.inst:
            self.inst.close()
            self.rm.close()
            self.connected = False

    def _handle_visa_error(self, e: pyvisa.VisaIOError):
        """Maps pyvisa errors to unified Instrumation exceptions."""
        from pyvisa import constants
        if e.error_code == constants.StatusCode.error_timeout:
            raise InstrumentTimeout(f"Instrument timeout: {e}")
        elif e.error_code in [constants.StatusCode.error_connection_lost, constants.StatusCode.error_inv_object]:
            raise ConnectionLost(f"Connection lost: {e}")
        else:
            raise InstrumentError(f"Instrument communication error: {e}")

    def write(self, command: str):
        if not self.inst:
             raise ConnectionLost("Not connected to instrument.")
        try:
            self.inst.write(command)
        except pyvisa.VisaIOError as e:
            self._handle_visa_error(e)

    def query(self, command: str) -> str:
        if not self.inst:
             raise ConnectionLost("Not connected to instrument.")
        try:
            return self.inst.query(command).strip()
        except pyvisa.VisaIOError as e:
            self._handle_visa_error(e)

    def get_id(self) -> str:
        return self.query("*IDN?")

    # Support legacy measure_voltage for backward compatibility
    def measure_voltage(self, channel=1) -> MeasurementResult:
        return MeasurementResult(float(self.query(f"MEAS:VOLT:DC? (@{channel})")), "V")

    def measure_frequency(self) -> MeasurementResult:
        return MeasurementResult(float(self.query("MEAS:FREQ?")), "Hz")

    def measure_duty_cycle(self) -> MeasurementResult:
        return MeasurementResult(float(self.query("MEAS:DUTY?")), "%")

    def measure_v_peak_to_peak(self) -> MeasurementResult:
        return MeasurementResult(float(self.query("MEAS:VPP?")), "Vpp")