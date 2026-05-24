"""Tests for the Frequency Counter driver (issue #86)."""

import os
from instrumation.factory import get_instrument
from instrumation.drivers.simulated import SimulatedFrequencyCounter
from instrumation.drivers.keysight import Keysight53230A
from instrumation.drivers.base import FrequencyCounter, MeasurementResult


def test_frequency_counter_base_class():
    """FrequencyCounter should be importable and have the expected abstract methods."""
    # Verify the abstract methods exist
    abstract_methods = {
        "measure_frequency", "measure_period", "measure_time_interval",
        "set_impedance", "set_trigger_level", "set_coupling", "set_auto_range",
    }
    for method in abstract_methods:
        assert hasattr(FrequencyCounter, method), f"Missing abstract method: {method}"


def test_simulated_counter_instantiation():
    """SimulatedFrequencyCounter should instantiate and connect."""
    counter = SimulatedFrequencyCounter("USB0::SIM::COUNTER::INSTR")
    counter.connect()
    assert counter.connected
    assert counter.identity["model"] == "SIM_COUNTER"
    counter.disconnect()


def test_simulated_counter_measure_frequency():
    """measure_frequency should return 10 MHz by default."""
    counter = SimulatedFrequencyCounter("USB0::SIM::COUNTER::INSTR")
    counter.connect()
    result = counter.measure_frequency()
    assert isinstance(result, MeasurementResult)
    assert result.unit == "Hz"
    assert result.value == 10e6
    counter.disconnect()


def test_simulated_counter_measure_period():
    """measure_period should return 100 ns by default."""
    counter = SimulatedFrequencyCounter("USB0::SIM::COUNTER::INSTR")
    counter.connect()
    result = counter.measure_period()
    assert isinstance(result, MeasurementResult)
    assert result.unit == "s"
    assert result.value == 100e-9
    counter.disconnect()


def test_simulated_counter_measure_time_interval():
    """measure_time_interval should return 50 ns."""
    counter = SimulatedFrequencyCounter("USB0::SIM::COUNTER::INSTR")
    counter.connect()
    result = counter.measure_time_interval("POS,1", "POS,2")
    assert isinstance(result, MeasurementResult)
    assert result.unit == "s"
    assert result.value == 50e-9
    counter.disconnect()


def test_simulated_counter_configuration():
    """Configuration methods should store values and print logs."""
    counter = SimulatedFrequencyCounter("USB0::SIM::COUNTER::INSTR")
    counter.connect()
    counter.set_impedance(50)
    assert counter._impedance == 50
    counter.set_trigger_level(1.5)
    assert counter._trigger_level == 1.5
    counter.set_coupling("AC")
    assert counter._coupling == "AC"
    counter.set_auto_range(False)
    assert counter._auto_range is False
    counter.disconnect()


def test_simulated_counter_context_manager():
    """SimulatedFrequencyCounter should work as a context manager."""
    with SimulatedFrequencyCounter("USB0::SIM::COUNTER::INSTR") as counter:
        result = counter.measure_frequency()
        assert result.value == 10e6
    assert not counter.connected


def test_keysight53230a_instantiation():
    """Keysight53230A should instantiate and have correct defaults."""
    counter = Keysight53230A("TCPIP::192.168.1.100::INSTR")
    assert counter.max_frequency == 20e9
    assert counter._active_channel == 1


def test_factory_digital_twin_mode():
    """Factory get_instrument with INSTRUMATION_MODE=SIM should return SimulatedFrequencyCounter."""
    os.environ["INSTRUMATION_MODE"] = "SIM"
    try:
        counter = get_instrument("AUTO", "COUNTER")
        assert isinstance(counter, SimulatedFrequencyCounter)
        assert counter.connected
        result = counter.measure_frequency()
        assert result.value == 10e6
        counter.disconnect()
    finally:
        os.environ["INSTRUMATION_MODE"] = ""


def test_simulated_counter_numeric_range():
    """measure_frequency with a numeric range string should still work."""
    counter = SimulatedFrequencyCounter("USB0::SIM::COUNTER::INSTR")
    counter.connect()
    # The simulated version ignores the range parameter but shouldn't crash
    result = counter.measure_frequency(range="100e6")
    assert isinstance(result, MeasurementResult)
    assert result.unit == "Hz"
    counter.disconnect()


def test_simulated_counter_measure_frequency_kwarg():
    """measure_frequency should accept range as keyword argument (like base class signature)."""
    counter = SimulatedFrequencyCounter("USB0::SIM::COUNTER::INSTR")
    counter.connect()
    result = counter.measure_frequency(range="AUTO")
    assert isinstance(result, MeasurementResult)
    assert result.value == 10e6
    counter.disconnect()
