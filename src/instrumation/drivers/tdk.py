from .base import PowerSupply
from .real import RealDriver

class TDKLambdaZPlus(RealDriver, PowerSupply):
    """Driver for TDK-Lambda Z+ Series Programmable Power Supplies (e.g., Z36-6).

    This driver supports setting and reading voltage and current, 
    as well as controlling the output state.
    """

    def set_voltage(self, voltage: float):
        """Sets the output voltage.

        Args:
            voltage (float): The voltage level to set in Volts.
        """
        self.inst.write(f":VOLT {voltage}")

    def get_voltage(self) -> float:
        """Reads back the actual output voltage.

        Returns:
            float: THE measured voltage in Volts.
        """
        return float(self.inst.query(":MEAS:VOLT?"))

    def set_current_limit(self, current: float):
        """Sets the output current limit.

        Args:
            current (float): The current limit to set in Amperes.
        """
        self.inst.write(f":CURR {current}")

    def get_current(self) -> float:
        """Reads back the actual output current.

        Returns:
            float: The measured current in Amperes.
        """
        return float(self.inst.query(":MEAS:CURR?"))

    def set_output(self, state: bool):
        """Enables (True) or disables (False) the output.

        Args:
            state (bool): True to enable, False to disable.
        """
        self.inst.write(f":OUTP {'ON' if state else 'OFF'}")

    def get_output(self) -> bool:
        """Returns the current output state.

        Returns:
            bool: True if output is ON, False if OFF.
        """
        state = self.inst.query(":OUTP?").strip()
        # Some returns "ON" or "1", handle both
        return state == "1" or state.upper() == "ON"
