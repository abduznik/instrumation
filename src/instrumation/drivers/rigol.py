from .base import SpectrumAnalyzer
from .registry import register_driver
from ..results import MeasurementResult

@register_driver("SA")
class RigolDSA(SpectrumAnalyzer):
    """Driver for Rigol DSA Series Spectrum Analyzers.

    Provides basic marker and peak search functionality for Rigol instruments.
    """
    def peak_search(self):
        """Performs a peak search and moves the active marker to the maximum peak."""
        # Rigol uses a slightly different syntax sometimes
        self.inst.write(":CALC:MARK:MAX") 

    def get_marker_amplitude(self) -> MeasurementResult:
        """Queries the amplitude of the current marker.

        Returns:
            MeasurementResult: The amplitude value in dBm.
        """
        # Rigol reading command
        val = self.inst.query(":CALC:MARK:Y?") 
        return MeasurementResult(float(val), "dBm")
