import pyvisa
from .base import InstrumentDriver, Multimeter

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
    def measure_voltage(self, channel=1) -> float:
        if self.inst:
             return float(self.inst.query(f"MEAS:VOLT:DC? (@{channel})"))
        return 0.0

    def measure_frequency(self) -> float:
        if self.inst:
            # SCPI command for frequency measurement
            return float(self.inst.query("MEAS:FREQ?"))
        return 0.0

    def measure_duty_cycle(self) -> float:
        if self.inst:
            # SCPI command for duty cycle measurement
            return float(self.inst.query("MEAS:DUTY?"))
        return 0.0

    def measure_v_peak_to_peak(self) -> float:
        if self.inst:
            # SCPI command for peak-to-peak voltage measurement
            return float(self.inst.query("MEAS:VPP?"))
        return 0.0