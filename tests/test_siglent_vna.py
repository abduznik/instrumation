import pytest
from unittest.mock import MagicMock, patch
from instrumation.drivers.siglent_vna import SiglentSNA5000A


@pytest.fixture
def mock_vna():
    with patch('pyvisa.ResourceManager'):
        driver = SiglentSNA5000A("TCPIP::1.2.3.25::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "0"
        driver.check_errors_enabled = False
        yield driver


def test_set_start_stop_frequency(mock_vna):
    mock_vna.set_start_frequency(1e9)
    mock_vna.inst.write.assert_any_call("SENS:FREQ:STAR 1000000000.0")
    mock_vna.set_stop_frequency(2e9)
    mock_vna.inst.write.assert_any_call("SENS:FREQ:STOP 2000000000.0")


def test_set_center_span(mock_vna):
    mock_vna.set_center_frequency(1.5e9)
    mock_vna.inst.write.assert_any_call("SENS:FREQ:CENT 1500000000.0")
    mock_vna.set_span(1e9)
    mock_vna.inst.write.assert_any_call("SENS:FREQ:SPAN 1000000000.0")


def test_set_points(mock_vna):
    mock_vna.set_points(201)
    mock_vna.inst.write.assert_any_call("SENS:SWE:POIN 201")


def test_set_if_bandwidth(mock_vna):
    mock_vna.set_if_bandwidth(1000.0)
    mock_vna.inst.write.assert_any_call("SENS:BAND 1000.0")


def test_set_power_level(mock_vna):
    mock_vna.set_power_level(-10.0)
    mock_vna.inst.write.assert_any_call("SOUR:POW -10.0")


def test_set_sweep_type(mock_vna):
    mock_vna.set_sweep_type("LOG")
    mock_vna.inst.write.assert_any_call("SENS:SWE:TYPE LOG")


def test_set_averaging(mock_vna):
    mock_vna.set_averaging(True, count=16)
    mock_vna.inst.write.assert_any_call("SENS:AVER ON")
    mock_vna.inst.write.assert_any_call("SENS:AVER:COUN 16")


def test_set_continuous(mock_vna):
    mock_vna.set_continuous(False)
    mock_vna.inst.write.assert_any_call("INIT:CONT OFF")


def test_set_parameter(mock_vna):
    mock_vna.set_parameter("S21", measurement_name="Trc1")
    mock_vna.inst.write.assert_any_call("CALC:PAR:SEL 'Trc1'")
    mock_vna.inst.write.assert_any_call("CALC:PAR:MOD S21")


def test_create_measurement(mock_vna):
    mock_vna.create_measurement("Trc1", "S11", window=1, trace=1)
    mock_vna.inst.write.assert_any_call("DISP:WIND1:STAT ON")
    mock_vna.inst.write.assert_any_call("CALC:PAR:DEF:EXT 'Trc1','S11'")
    mock_vna.inst.write.assert_any_call("DISP:WIND1:TRAC1:FEED 'Trc1'")


def test_get_trace_data(mock_vna):
    mock_vna.inst.query_binary_values.return_value = [1.0, 2.0, 3.0]
    data = mock_vna.get_trace_data("MyTrace")
    mock_vna.inst.write.assert_any_call("CALC:PAR:SEL 'MyTrace'")
    mock_vna.inst.query_binary_values.assert_called_with("CALC:DATA? FDATA", datatype='f', is_big_endian=False)
    assert data.value == [1.0, 2.0, 3.0]
    assert data.unit == "dB"


def test_get_complex_trace(mock_vna):
    mock_vna.inst.query_binary_values.return_value = [1.0, 2.0, 3.0, 4.0]
    data = mock_vna.get_complex_trace("MyTrace")
    assert data.value == [complex(1.0, 2.0), complex(3.0, 4.0)]
    assert data.unit == "IQ"


def test_get_smith_data(mock_vna):
    mock_vna.inst.query_binary_values.return_value = [1.0, 0.5]
    data = mock_vna.get_smith_data("MyTrace")
    mock_vna.inst.write.assert_any_call("CALC:FORM SMITH")
    assert data.value == [complex(1.0, 0.5)]
    assert data.unit == "Z"


def test_peak_search(mock_vna):
    mock_vna.peak_search(marker=1)
    mock_vna.inst.write.assert_any_call("CALC:MARK1:STAT ON")
    mock_vna.inst.write.assert_any_call("CALC:MARK1:FUNC:SEL MAX")
    mock_vna.inst.write.assert_any_call("CALC:MARK1:FUNC:EXEC")


def test_get_marker_x_y(mock_vna):
    mock_vna.inst.query.return_value = "1500000000.0"
    assert mock_vna.get_marker_x(1) == 1500000000.0
    mock_vna.inst.query.return_value = "-3.5,0.0"
    assert mock_vna.get_marker_y(1) == -3.5


def test_save_load_state_appends_extension(mock_vna):
    mock_vna.save_state("mystate")
    mock_vna.inst.write.assert_any_call("MMEM:STOR:STAT 'mystate.sta'")
    mock_vna.load_state("mystate")
    mock_vna.inst.write.assert_any_call("MMEM:LOAD:STAT 'mystate.sta'")


def test_wait_for_sweep(mock_vna):
    mock_vna.wait_for_sweep()
    mock_vna.inst.query.assert_any_call("*OPC?")
