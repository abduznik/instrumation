from .base import Oscilloscope
from .registry import register_driver
from ..results import MeasurementResult

@register_driver("SCOPE")
class TektronixTDS(Oscilloscope):
    def connect(self):
        # Assuming resource is a pyvisa Resource object
        if self.resource:
            self.connected = True

    def disconnect(self):
        if self.resource:
            self.resource.close()
        self.connected = False

    def get_id(self) -> str:
        if self.resource:
            return self.resource.query("*IDN?").strip()
        return "Not Connected"

    def run(self):
        """Starts acquisition."""
        if self.resource:
            self.resource.write(":ACQUIRE:STATE ON")

    def stop(self):
        """Stops acquisition."""
        if self.resource:
            self.resource.write(":ACQUIRE:STATE OFF")

    def single(self):
        """Sets the oscilloscope to single acquisition mode."""
        # Tektronix TDS usually uses ACQUIRE:STOPAFTER SEQUENCE for single shot behavior
        # or just STOP then RUN? The issue didn't specify the command for single,
        # but common SCPI is :ACQUIRE:STOPAFTER SEQUENCE
        if self.resource:
            self.resource.write(":ACQUIRE:STOPAFTER SEQUENCE")
            self.resource.write(":ACQUIRE:STATE ON")

    def get_waveform(self, channel: int) -> MeasurementResult:
        """Returns the waveform data for the specified channel."""
        if not self.resource:
            return MeasurementResult([], "V")

        # Set source
        self.resource.write(f":DATA:SOURCE CH{channel}")
        
        # Ensure ASCII encoding for simplicity in this driver
        self.resource.write(":DATA:ENC ASC")
        
        # Get width in bytes (1 or 2) - mostly 1 for simple usage
        self.resource.write(":DATA:WIDTH 1")
        
        # Get the data
        # :CURVE? returns comma separated values in ASCII mode
        raw_data = self.resource.query(":CURVE?")
        
        try:
            # Parse CSV string to list of floats
            data = [float(x) for x in raw_data.split(',')]
            return MeasurementResult(data, "V")
        except ValueError:
            print(f"Error parsing waveform data: {raw_data[:20]}...")
            return MeasurementResult([], "V")

    # Implement other abstract methods from InstrumentDriver
    def measure_frequency(self) -> MeasurementResult:
        # Placeholder or use generic MEAS command
        if self.resource:
             return MeasurementResult(float(self.resource.query("MEASU:IMM:VAL?")), "Hz")
        return MeasurementResult(0.0, "Hz")

    def measure_duty_cycle(self) -> MeasurementResult:
         # Placeholder
         return MeasurementResult(0.0, "%")

    def measure_v_peak_to_peak(self) -> MeasurementResult:
         # Placeholder
         return MeasurementResult(0.0, "Vpp")
