from .base import SpectrumAnalyzer

class KeysightMXA(SpectrumAnalyzer):
    def peak_search(self):
        # Keysight command for Peak Search
        self.inst.write(":CALC:MARK1:MAX") 

    def get_marker_amplitude(self):
        # Keysight command to read Y-axis value
        val = self.inst.query(":CALC:MARK1:Y?")
        return float(val)
