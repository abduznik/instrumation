from .base import InstrumentDriver
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("POWERMETER")
class YokogawaWT310(RealDriver, InstrumentDriver):
    """Driver for Yokogawa WT310/WT310HC/WT332/WT333 Digital Power Meters.

    Uses Yokogawa's ``:NUMeric[:NORMal]:ITEM<x>`` output-item
    configuration model: each numeric output slot (1-255) is assigned
    a function (``U``=voltage, ``I``=current, ``P``=active power,
    ``S``=apparent power, ``Q``=reactive power, ``LAMBda``=power
    factor, etc.) and element (1-3 for multi-element models), then
    ``:NUMeric[:NORMal]:VALue?`` reads back all configured items as a
    single comma-separated response -- distinct from a per-quantity
    ``MEASure:<FUNC>?`` query used by DMM-style instruments.

    SCPI Reference (WT310 Communication Interface Manual):
        - :NUMeric[:NORMal]:ITEM<x> {<Function>[,<Element>][,<Order>]}
        - :NUMeric[:NORMal]:ITEM<x>?
        - :NUMeric[:NORMal]:VALue?          — comma-separated readout
        - :NUMeric[:NORMal]:PRESet <1-4>    — preset output item patterns
        - :NUMeric:HOLD {ON|OFF}            — freeze readout for atomic multi-item reads
        - :RATE {100MS|250MS|500MS|1S|2S|5S}
        - :INPut:VOLTage:RANGe / :INPut:CURRent:RANGe
        - :INTEGrate:MODE / :STARt / :STOP / :RESet
        - *CAL?                              — zero calibration
    """

    def set_output_item(self, index: int, function: str, element: int = 1) -> None:
        """Configures numeric output slot `index` (1-255) with a function/element."""
        self.safe_send(f"NUM:ITEM{index} {function.upper()},{element}")

    def set_output_preset(self, pattern: int) -> None:
        """Selects one of the 4 factory output-item presets."""
        if pattern not in (1, 2, 3, 4):
            raise ValueError("pattern must be 1-4")
        self.safe_send(f"NUM:PRES {pattern}")

    def set_hold(self, state: bool) -> None:
        """Freezes numeric readout so multiple items reflect a single instant."""
        self.safe_send(f"NUM:HOLD {'ON' if state else 'OFF'}")

    def read_values(self) -> MeasurementResult:
        """Reads back all currently configured numeric output items."""
        resp = self.query_ascii("NUM:VAL?")
        values = [float(v) for v in resp.split(",") if v.strip()]
        return MeasurementResult(values, "mixed")

    def measure_voltage(self, element: int = 1) -> MeasurementResult:
        self.set_output_item(1, "U", element)
        val = float(self.query_ascii("NUM:VAL?").split(",")[0])
        return MeasurementResult(val, "V")

    def measure_current(self, element: int = 1) -> MeasurementResult:
        self.set_output_item(1, "I", element)
        val = float(self.query_ascii("NUM:VAL?").split(",")[0])
        return MeasurementResult(val, "A")

    def measure_active_power(self, element: int = 1) -> MeasurementResult:
        self.set_output_item(1, "P", element)
        val = float(self.query_ascii("NUM:VAL?").split(",")[0])
        return MeasurementResult(val, "W")

    def measure_power_factor(self, element: int = 1) -> MeasurementResult:
        self.set_output_item(1, "LAMB", element)
        val = float(self.query_ascii("NUM:VAL?").split(",")[0])
        return MeasurementResult(val, "")

    def set_update_rate(self, rate: str) -> None:
        """Sets the data update interval: 100MS, 250MS, 500MS, 1S, 2S, or 5S."""
        self.safe_send(f"RATE {rate.upper()}")

    def zero_calibrate(self) -> str:
        """Executes zero-level compensation (*CAL?) and returns the result code."""
        return self.query("*CAL?")

    def start_integration(self) -> None:
        self.write("INTEG:STAR")

    def stop_integration(self) -> None:
        self.write("INTEG:STOP")

    def reset_integration(self) -> None:
        self.write("INTEG:RES")

    def shutdown_safety(self) -> None:
        self.sync_config()
