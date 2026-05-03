import os
from instrumation.factory import get_instrument, load_plugins

def test_plugin_loading(tmp_path):
    """Test that a driver can be loaded from a plugin directory."""
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    
    # Create a mock driver plugin inheriting from SimulatedBaseDriver to satisfy abstract methods
    plugin_content = """
from instrumation.drivers.simulated import SimulatedBaseDriver
from instrumation.drivers.base import Multimeter
from instrumation.drivers.registry import register_driver
from instrumation.results import MeasurementResult

@register_driver("PLUGIN_DMM")
class MyPluginDMM(SimulatedBaseDriver, Multimeter):
    def measure_voltage(self, ac=False): return MeasurementResult(123.45, "V")
    def measure_resistance(self, four_wire=False): return MeasurementResult(0, "Ohm")
    def measure_current(self, ac=False): return MeasurementResult(0, "A")
    def configure_voltage_dc(self): pass
    def configure_voltage_ac(self): pass
    def set_auto_range(self, state): pass
    def get_id(self): return "MY_PLUGIN_DMM"
"""
    plugin_file = plugin_dir / "my_plugin.py"
    plugin_file.write_text(plugin_content)
    
    load_plugins(str(plugin_dir))
    
    os.environ["INSTRUMATION_MODE"] = "REAL"
    try:
        instr = get_instrument("DUMMY", "PLUGIN_DMM")
        assert instr.__class__.__name__ == "MyPluginDMM"
        assert instr.get_id() == "MY_PLUGIN_DMM"
        assert instr.measure_voltage().value == 123.45
    finally:
        os.environ["INSTRUMATION_MODE"] = "SIM"

def test_plugin_loading_simulated(tmp_path):
    """Test that a simulated driver can be loaded from a plugin directory."""
    plugin_dir = tmp_path / "plugins_sim"
    plugin_dir.mkdir()
    
    plugin_content = """
from instrumation.drivers.simulated import SimulatedBaseDriver
from instrumation.drivers.base import Multimeter
from instrumation.drivers.registry import register_driver
from instrumation.results import MeasurementResult

@register_driver("SIM_PLUGIN_DMM")
class SimulatedPluginDMM(SimulatedBaseDriver, Multimeter):
    def measure_voltage(self, ac=False): return MeasurementResult(0, "V")
    def measure_resistance(self, four_wire=False): return MeasurementResult(0, "Ohm")
    def measure_current(self, ac=False): return MeasurementResult(0, "A")
    def configure_voltage_dc(self): pass
    def configure_voltage_ac(self): pass
    def set_auto_range(self, state): pass
"""
    plugin_file = plugin_dir / "my_sim_plugin.py"
    plugin_file.write_text(plugin_content)
    
    load_plugins(str(plugin_dir))
    
    os.environ["INSTRUMATION_MODE"] = "SIM"
    get_instrument("DUMMY", "SIM_PLUGIN_DMM")
    
    from instrumation.drivers.registry import DriverRegistry
    drivers = DriverRegistry.get_drivers_by_type("SIM_PLUGIN_DMM")
    assert any(d.__name__ == "SimulatedPluginDMM" for d in drivers)
