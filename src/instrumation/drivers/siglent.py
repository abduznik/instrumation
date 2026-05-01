from .base import Oscilloscope
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult

@register_driver("SCOPE")
class SiglentSDS(RealDriver, Oscilloscope):
    """Driver for Siglent SDS Series Oscilloscopes (SDS1000, SDS2000, etc.).

    This driver provides support for basic acquisition control and waveform retrieval
    using standard Siglent SCPI commands.
    """

    def run(self):
        """Starts acquisition."""
        if self.inst:
            # For Siglent, ARM starts acquisition in current mode
            self.inst.write("ARM")

    def stop(self):
        """Stops acquisition."""
        if self.inst:
            self.inst.write("STOP")

    def single(self):
        """Sets the oscilloscope to single acquisition mode."""
        if self.inst:
            self.inst.write("SING")

    def get_waveform(self, channel: int) -> MeasurementResult:
        """Returns the waveform data for the specified channel.

        Args:
            channel (int): The channel number (e.g., 1, 2).

        Returns:
            MeasurementResult: The waveform data points as raw code values.
        """
        if not self.inst:
            return MeasurementResult([], "V")

        # Request data for the specified channel
        # DAT2 returns only the data block without the descriptor
        query_cmd = f"C{channel}:WF? DAT2"
        
        # Siglent response format for C<n>:WF? DAT2:
        # C<n>:WF DAT2,#9000000000<length><data>\n\n
        
        # Manual read to skip the prefix "C<n>:WF DAT2,"
        self.inst.write(query_cmd)
        
        # Calculate prefix length: C<channel>:WF DAT2,
        prefix = f"C{channel}:WF DAT2,"
        self.inst.read_bytes(len(prefix))
        
        # Now use PyVISA's query_binary_values to parse the IEEE header and data
        data = self.inst.query_binary_values("", datatype='b', container=list)
        
        # Return as list of floats wrapped in MeasurementResult
        data_floats = [float(b) for b in data]
        return MeasurementResult(data_floats, "V")

    # Implement abstract methods from InstrumentDriver
    def measure_frequency(self) -> MeasurementResult:
        """Measures the frequency on Channel 1.

        Returns:
            MeasurementResult: The measured frequency in Hz.
        """
        if self.inst:
             # Query parameter value for frequency
             val = self.inst.query("C1:PAVA? FREQ").split(',')[-1]
             # Parse value (e.g., '1.23e+03V' or '1.23e+03Hz')
             return MeasurementResult(float(val.strip().rstrip('VHz ')), "Hz")
        return MeasurementResult(0.0, "Hz")

    def measure_duty_cycle(self) -> MeasurementResult:
        """Measures the duty cycle on Channel 1.

        Returns:
            MeasurementResult: The duty cycle in percent (0-100).
        """
        if self.inst:
             val = self.inst.query("C1:PAVA? DUTY").split(',')[-1]
             return MeasurementResult(float(val.strip().rstrip('% ')), "%")
        return MeasurementResult(0.0, "%")

    def measure_v_peak_to_peak(self) -> MeasurementResult:
        """Measures the peak-to-peak voltage on Channel 1.

        Returns:
            MeasurementResult: The peak-to-peak voltage in Volts.
        """
        if self.inst:
               val = self.inst.query("C1:PAVA? PKPK").split(',')[-1]
               return MeasurementResult(float(val.strip().rstrip('V ')), "Vpp")
        return MeasurementResult(0.0, "Vpp")
