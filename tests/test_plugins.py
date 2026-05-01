import pytest
import os
import shutil
from instrumation.factory import get_instrument, load_plugins
from instrumation.drivers.base import Multimeter

def test_plugin_loading(tmp_path):
    """Test that a driver can be loaded from a plugin directory."""
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    
    # Create a mock driver plugin
    plugin_content = """
from instrumation.drivers.base import Multimeter
from instrumation.drivers.registry import register_driver
from instrumation.results import MeasurementResult

@register_driver("PLUGIN_DMM")
class MyPluginDMM(Multimeter):
    def __init__(self, resource):
        super().__init__(resource)
    def connect(self): self.connected = True
    def disconnect(self): self.connected = False
    def get_id(self): return "MY_PLUGIN_DMM"
    def measure_voltage(self): return MeasurementResult(123.45, "V")
    def measure_resistance(self): return MeasurementResult(0, "Ohm")
    def measure_frequency(self): return MeasurementResult(0, "Hz")
    def measure_duty_cycle(self): return MeasurementResult(0, "%")
    def measure_v_peak_to_peak(self): return MeasurementResult(0, "Vpp")
"""
    plugin_file = plugin_dir / "my_plugin.py"
    plugin_file.write_text(plugin_content)
    
    # Load plugins from the temporary directory
    load_plugins(str(plugin_dir))
    
    # In real mode (not SIM), our factory should find this driver
    os.environ["INSTRUMATION_MODE"] = "REAL"
    try:
        instr = get_instrument("DUMMY", "PLUGIN_DMM")
        assert instr.__class__.__name__ == "MyPluginDMM"
        assert instr.get_id() == "MY_PLUGIN_DMM"
        assert instr.measure_voltage().value == 123.45
    finally:
        # Reset mode
        os.environ["INSTRUMATION_MODE"] = "SIM"

def test_plugin_loading_simulated(tmp_path):
    """Test that a simulated driver can be loaded from a plugin directory."""
    plugin_dir = tmp_path / "plugins_sim"
    plugin_dir.mkdir()
    
    # Create a mock simulated driver plugin
    plugin_content = """
from instrumation.drivers.simulated import SimulatedBaseDriver
from instrumation.drivers.base import Multimeter
from instrumation.drivers.registry import register_driver

@register_driver("SIM_PLUGIN_DMM")
class SimulatedPluginDMM(SimulatedBaseDriver, Multimeter):
    def get_id(self): return "SIM_PLUGIN_DMM"
    def connect(self): self.connected = True
    def disconnect(self): self.connected = False
    def measure_voltage(self): return MeasurementResult(0, "V")
    def measure_resistance(self): return MeasurementResult(0, "Ohm")
"""
    plugin_file = plugin_dir / "my_sim_plugin.py"
    plugin_file.write_text(plugin_content)
    
    load_plugins(str(plugin_dir))
    
    os.environ["INSTRUMATION_MODE"] = "SIM"
    instr = get_instrument("DUMMY", "SIM_PLUGIN_DMM")
    
    from instrumation.drivers.registry import DriverRegistry
    drivers = DriverRegistry.get_drivers_by_type("SIM_PLUGIN_DMM")
    assert any(d.__name__ == "SimulatedPluginDMM" for d in drivers)
