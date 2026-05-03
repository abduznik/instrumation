import os
from instrumation.factory import get_instrument
from instrumation.results import MeasurementResult

def test_multimeter_voltage_result_type():
    """Test that measure_voltage returns a MeasurementResult object."""
    os.environ["INSTRUMATION_MODE"] = "SIM"
    
    with get_instrument("DUMMY", "DMM") as dmm:
        res = dmm.measure_voltage()
        assert isinstance(res, MeasurementResult)
        assert isinstance(res.value, float)
        assert res.unit == "V"
        assert res.status == "OK"

def test_spectrum_analyzer_amplitude_result_type():
    """Test that get_marker_amplitude returns a MeasurementResult object."""
    os.environ["INSTRUMATION_MODE"] = "SIM"
    
    with get_instrument("DUMMY", "SA") as sa:
        res = sa.get_marker_amplitude()
        assert isinstance(res, MeasurementResult)
        assert isinstance(res.value, float)
        assert res.unit == "dBm"

def test_network_analyzer_trace_result_type():
    """Test that get_trace_data returns a MeasurementResult object with list value."""
    os.environ["INSTRUMATION_MODE"] = "SIM"
    
    with get_instrument("DUMMY", "NA") as na:
        res = na.get_trace_data("S21")
        assert isinstance(res, MeasurementResult)
        assert isinstance(res.value, list)
        assert len(res.value) == 201
        assert res.unit == "dB"
