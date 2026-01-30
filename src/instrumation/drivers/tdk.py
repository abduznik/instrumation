from .base import PowerSupply
from .real import RealDriver

class TDKLambdaZPlus(RealDriver, PowerSupply):
    """
    Driver for TDK-Lambda Z+ Series Programmable Power Supplies (e.g., Z36-6).
    """

    def set_voltage(self, voltage: float):
        """Sets the output voltage."""
        self.inst.write(f":VOLT {voltage}")

    def get_voltage(self) -> float:
        """Reads back the actual output voltage."""
        return float(self.inst.query(":MEAS:VOLT?"))

    def set_current_limit(self, current: float):
        """Sets the output current limit."""
        self.inst.write(f":CURR {current}")

    def get_current(self) -> float:
        """Reads back the actual output current."""
        return float(self.inst.query(":MEAS:CURR?"))

    def set_output(self, state: bool):
        """Enables (True) or disables (False) the output."""
        self.inst.write(f":OUTP {'ON' if state else 'OFF'}")

    def get_output(self) -> bool:
        """Returns True if output is ON, False if OFF."""
        state = self.inst.query(":OUTP?").strip()
        # Some returns "ON" or "1", handle both
        return state == "1" or state.upper() == "ON"
