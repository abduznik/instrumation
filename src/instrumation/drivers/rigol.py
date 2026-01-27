from .base import SpectrumAnalyzer

class RigolDSA(SpectrumAnalyzer):
    def peak_search(self):
        # Rigol uses a slightly different syntax sometimes
        self.inst.write(":CALC:MARK:MAX") 

    def get_marker_amplitude(self):
        # Rigol reading command
        val = self.inst.query(":CALC:MARK:Y?") 
        return float(val)
