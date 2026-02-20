from .base import Oscilloscope
from .real import RealDriver

class SiglentSDS(RealDriver, Oscilloscope):
    """Driver for Siglent SDS Series Oscilloscopes (SDS1000, SDS2000, etc.).

    This driver uses SCPI commands to control the oscilloscope and retrieve waveform data.
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

    def get_waveform(self, channel: int) -> list[float]:
        """Returns the waveform data for the specified channel.

        Args:
            channel (int): The channel number (1, 2, 3, or 4).

        Returns:
            list[float]: The waveform data points.
        """
        if not self.inst:
            return []

        # Request data for the specified channel
        # DAT2 returns only the data block without the descriptor (for some models)
        # However, Siglent often returns a header anyway.
        query_cmd = f"C{channel}:WF? DAT2"
        
        # Siglent response format for C<n>:WF? DAT2:
        # C<n>:WF DAT2,#9000000000<length><data>\n\n
        # We use query_binary_values if possible, but let's do it manually for compatibility
        
        raw_response = self.inst.query_binary_values(query_cmd, datatype='b', container=list)
        
        # Note: query_binary_values handles the #<n><length> part.
        # But Siglent adds "C<n>:WF DAT2," before the #.
        # PyVISA's query_binary_values might struggle if there's text before the #.
        
        # Alternative approach: manual read
        self.inst.write(query_cmd)
        header = self.inst.read_bytes(len(f"C{channel}:WF DAT2,"))
        # Now the pointer should be at #
        data = self.inst.query_binary_values("", datatype='b', container=list)
        
        # Some models might return actual floats, but DAT2 usually returns raw bytes (0-255)
        # We convert to float for the interface requirement
        return [float(b) for b in data]

    # Implement other abstract methods from InstrumentDriver if needed, 
    # though RealDriver handles most.
    def measure_frequency(self) -> float:
        if self.inst:
             # Siglent specific measure command
             return float(self.inst.query("C1:PAVA? FREQ").split(',')[-1].split('V')[0])
        return 0.0

    def measure_duty_cycle(self) -> float:
         if self.inst:
             return float(self.inst.query("C1:PAVA? DUTY").split(',')[-1].split('%')[0])
         return 0.0

    def measure_v_peak_to_peak(self) -> float:
         if self.inst:
              return float(self.inst.query("C1:PAVA? PKPK").split(',')[-1].split('V')[0])
         return 0.0
