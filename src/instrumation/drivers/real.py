import pyvisa
from .base import InstrumentDriver, Multimeter
from ..results import MeasurementResult

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
            raise ConnectionError(f"Failed to connect to {self.resource}: {e}")

    def disconnect(self):
        if self.inst:
            self.inst.close()
            self.rm.close()
            self.connected = False

    def get_id(self) -> str:
        if self.inst:
            return self.inst.query("*IDN?").strip()
        return "Not Connected"

    # Support legacy measure_voltage for backward compatibility
    def measure_voltage(self, channel=1) -> MeasurementResult:
        if self.inst:
             return MeasurementResult(float(self.inst.query(f"MEAS:VOLT:DC? (@{channel})")), "V")
        return MeasurementResult(0.0, "V")

    def measure_frequency(self) -> MeasurementResult:
        if self.inst:
            # SCPI command for frequency measurement
            return MeasurementResult(float(self.inst.query("MEAS:FREQ?")), "Hz")
        return MeasurementResult(0.0, "Hz")

    def measure_duty_cycle(self) -> MeasurementResult:
        if self.inst:
            # SCPI command for duty cycle measurement
            return MeasurementResult(float(self.inst.query("MEAS:DUTY?")), "%")
        return MeasurementResult(0.0, "%")

    def measure_v_peak_to_peak(self) -> MeasurementResult:
        if self.inst:
            # SCPI command for peak-to-peak voltage measurement
            return MeasurementResult(float(self.inst.query("MEAS:VPP?")), "Vpp")
        return MeasurementResult(0.0, "Vpp")