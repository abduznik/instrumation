from typing import List
from .base import Multimeter, PowerSupply
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult

@register_driver("DMM")
class Keithley2000(RealDriver, Multimeter):
    """Driver for Keithley 2000 Series Digital Multimeters."""

    def preset(self, automation_optimized: bool = True) -> None:
        self.write("*RST")
        self.wait_ready()

    def configure_voltage_dc(self) -> None:
        self.safe_send(":CONF:VOLT:DC")

    def configure_voltage_ac(self) -> None:
        self.safe_send(":CONF:VOLT:AC")

    def measure_voltage(self, ac: bool = False) -> MeasurementResult:
        self.configure_voltage_ac() if ac else self.configure_voltage_dc()
        val = self.query_ascii(":READ?")
        return MeasurementResult(float(val.split(',')[0]), "V")

    def measure_resistance(self, four_wire: bool = False) -> MeasurementResult:
        cmd = ":CONF:FRES" if four_wire else ":CONF:RES"
        self.safe_send(cmd)
        val = self.query_ascii(":READ?")
        return MeasurementResult(float(val.split(',')[0]), "Ohm")

    def measure_current(self, ac: bool = False) -> MeasurementResult:
        cmd = ":CONF:CURR:AC" if ac else ":CONF:CURR:DC"
        self.safe_send(cmd)
        val = self.query_ascii(":READ?")
        return MeasurementResult(float(val.split(',')[0]), "A")

    def set_auto_range(self, state: bool) -> None:
        val = "ON" if state else "OFF"
        self.safe_send(f":VOLT:RANG:AUTO {val}")

    def measure_frequency(self) -> MeasurementResult:
        val = self.query_ascii(":MEAS:FREQ?")
        return MeasurementResult(float(val.split(',')[0]), "Hz")

    def measure_duty_cycle(self) -> MeasurementResult:
        self._unsupported_feature("Duty Cycle")
        return MeasurementResult(0.0, "%")

    def measure_v_peak_to_peak(self) -> MeasurementResult:
        self._unsupported_feature("Vpp")
        return MeasurementResult(0.0, "V")

    def shutdown_safety(self) -> None:
        self.set_auto_range(True)
        self.sync_config()

@register_driver("DMM")
@register_driver("PSU")
class Keithley2400(Keithley2000, PowerSupply):
    """Driver for Keithley 2400 Series SourceMeters (SMU).

    Operates as both a PowerSupply (source) and Multimeter (measure),
    making it a true Source Measure Unit.
    """

    def __init__(self, resource: str) -> None:
        super().__init__(resource)
        self.max_voltage = 210.0
        self.max_power_dbm = -999
        self._source_mode = "VOLT"

    def preset(self, automation_optimized: bool = True) -> None:
        self.write("*RST")
        self.safe_send(":SOUR:CLE:AUTO ON")
        self.wait_ready()

    # ── Source functions (PowerSupply) ─────────────────────────

    def set_voltage(self, voltage: float) -> None:
        self._validate_frequency(voltage)
        self._source_mode = "VOLT"
        self.safe_send(f":SOUR:VOLT {voltage}")

    def get_voltage(self) -> float:
        return float(self.query_ascii(":SOUR:VOLT?"))

    def set_current_limit(self, current: float) -> None:
        self._source_mode = "VOLT"
        self.safe_send(f":SOUR:CURR {current}")

    def set_current(self, current: float) -> None:
        self._source_mode = "CURR"
        self.safe_send(f":SOUR:CURR {current}")

    def get_current(self) -> MeasurementResult:
        return MeasurementResult(float(self.query_ascii(":SENS:CURR:DC?")), "A")

    def set_output(self, state: bool) -> None:
        self.safe_send(f":OUTP {'ON' if state else 'OFF'}")

    def get_output(self) -> bool:
        val = self.query_ascii(":OUTP?").strip()
        return val == "1"

    def set_ovp(self, voltage: float) -> None:
        self.safe_send(f":SOUR:VOLT:PROT {voltage}")

    def set_ocp(self, current: float) -> None:
        self.safe_send(f":SOUR:CURR:PROT {current}")

    def measure_voltage_actual(self) -> MeasurementResult:
        return self.measure_voltage()

    def clear_protection(self) -> None:
        self.safe_send(":SOUR:CLE:IMM")

    def set_voltage_range(self, voltage_range: float) -> None:
        self.safe_send(f":SOUR:VOLT:RANG {voltage_range}")

    def set_current_range(self, current_range: float) -> None:
        self.safe_send(f":SOUR:CURR:RANG {current_range}")

    def get_mode(self) -> str:
        val = self.query_ascii(":SOUR:FUNC?").strip().upper()
        if "VOLT" in val:
            return "CV"
        if "CURR" in val:
            return "CC"
        return "OFF"

    def measure_power(self) -> MeasurementResult:
        v = float(self.query_ascii(":MEAS:VOLT:DC?"))
        i = float(self.query_ascii(":MEAS:CURR:DC?"))
        return MeasurementResult(v * i, "W")

    # ── Measure functions (Multimeter) ─────────────────────────

    def configure_voltage_dc(self) -> None:
        self.safe_send(':SENS:FUNC "VOLT:DC"')

    def configure_voltage_ac(self) -> None:
        self._unsupported_feature("AC Voltage on 2400")
        self.safe_send(':SENS:FUNC "VOLT:DC"')

    def measure_voltage(self, ac: bool = False) -> MeasurementResult:
        if ac:
            self._unsupported_feature("AC Voltage")
        self.safe_send(':SENS:FUNC "VOLT:DC"')
        val = self.query_ascii(":READ?")
        # 2400 returns 4 values: V, I, RES, TIME
        return MeasurementResult(float(val.split(',')[0]), "V")

    def measure_resistance(self, four_wire: bool = False) -> MeasurementResult:
        self.safe_send(':SENS:FUNC "RES"')
        if four_wire:
            self.safe_send(':SYST:RSEN ON')
        else:
            self.safe_send(':SYST:RSEN OFF')
        val = self.query_ascii(":MEAS:RES?")
        return MeasurementResult(float(val.split(',')[2]), "Ohm")

    def measure_current(self, ac: bool = False) -> MeasurementResult:
        if ac:
            self._unsupported_feature("AC Current")
        self.safe_send(':SENS:FUNC "CURR:DC"')
        val = self.query_ascii(":READ?")
        return MeasurementResult(float(val.split(',')[1]), "A")

    def set_auto_range(self, state: bool) -> None:
        val = "ON" if state else "OFF"
        self.safe_send(f":SOUR:VOLT:RANG:AUTO {val}")

    def shutdown_safety(self) -> None:
        self.set_output(False)
        self.safe_send(":SOUR:VOLT 0")
        self.safe_send(":SOUR:CURR 0")
        self.sync_config()

    # ── Sweep / Step Helpers (GH #202) ───────────────────────────

    def configure_sweep_linear(
        self,
        start: float,
        stop: float,
        steps: int,
        source: str = "VOLT",
        delay: float = 0.01,
    ) -> None:
        """Configure a linear sweep on the given source (VOLT or CURR).

        Parameters
        ----------
        start : float
            Sweep start value.
        stop : float
            Sweep stop value.
        steps : int
            Number of steps (2 -- 1001).
        source : str
            Source function: ``"VOLT"`` or ``"CURR"``.
        delay : float
            Inter-step delay in seconds (0 -- 10).
        """
        src = source.upper()
        if src not in ("VOLT", "CURR"):
            raise ValueError(f"Invalid sweep source '{source}'. Must be VOLT or CURR")
        if steps < 2 or steps > 1001:
            raise ValueError(f"Steps must be 2--1001, got {steps}")
        self._source_mode = src
        self.safe_send(f":SOUR:FUNC {src}")
        self.safe_send(":SOUR:SWEEP:TYPE LIN")
        self.safe_send(f":SOUR:{src}:START {start}")
        self.safe_send(f":SOUR:{src}:STOP {stop}")
        self.safe_send(f":SOUR:{src}:STEP {steps}")
        self.safe_send(f":SOUR:DEL {delay}")

    def configure_sweep_log(
        self,
        start: float,
        stop: float,
        steps: int,
        source: str = "VOLT",
        delay: float = 0.01,
    ) -> None:
        """Configure a logarithmic sweep on the given source.

        Parameters mirror :meth:`configure_sweep_linear` but the step
        distribution is logarithmic (useful for impedance / capacitance
        sweeps).
        """
        src = source.upper()
        if src not in ("VOLT", "CURR"):
            raise ValueError(f"Invalid sweep source '{source}'. Must be VOLT or CURR")
        if steps < 2 or steps > 1001:
            raise ValueError(f"Steps must be 2--1001, got {steps}")
        if start <= 0 or stop <= 0:
            raise ValueError("Log sweep requires positive start and stop values")
        self._source_mode = src
        self.safe_send(f":SOUR:FUNC {src}")
        self.safe_send(":SOUR:SWEEP:TYPE LOG")
        self.safe_send(f":SOUR:{src}:START {start}")
        self.safe_send(f":SOUR:{src}:STOP {stop}")
        self.safe_send(f":SOUR:{src}:STEP {steps}")
        self.safe_send(f":SOUR:DEL {delay}")

    def configure_sweep_list(self, values: List[float], source: str = "VOLT", delay: float = 0.01) -> None:
        """Configure a custom list sweep with arbitrary source values.

        Parameters
        ----------
        values : list of float
            Source values to step through in order.
        source : str
            Source function: ``"VOLT"`` or ``"CURR"``.
        delay : float
            Inter-step delay in seconds.
        """
        src = source.upper()
        if src not in ("VOLT", "CURR"):
            raise ValueError(f"Invalid sweep source '{source}'. Must be VOLT or CURR")
        if len(values) < 2:
            raise ValueError("List sweep requires at least 2 values")
        self._source_mode = src
        self.safe_send(f":SOUR:FUNC {src}")
        self.safe_send(":SOUR:SWEEP:TYPE LIST")
        list_str = ",".join(str(v) for v in values)
        self.safe_send(f":SOUR:{src}:LIST {list_str}")
        self.safe_send(f":SOUR:DEL {delay}")

    def execute_sweep(self) -> List[MeasurementResult]:
        """Execute the previously configured sweep and return all data points.

        Returns a list of :class:`MeasurementResult` objects — one per
        step — containing the measured value (V, A, or Ohm) at each
        source point.
        """
        self.set_output(True)
        self.safe_send(":INIT")
        self.wait_ready()
        raw = self.query_ascii(":FETC?")
        self.set_output(False)
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        unit = "V" if self._source_mode == "VOLT" else "A"
        return [MeasurementResult(float(p), unit) for p in parts]

    def step_sweep(
        self,
        start: float,
        stop: float,
        steps: int,
        source: str = "VOLT",
        delay: float = 0.01,
    ) -> List[MeasurementResult]:
        """Convenience: configure + execute a linear sweep in one call.

        Combines :meth:`configure_sweep_linear` and
        :meth:`execute_sweep` for the common IV-curve use case.
        """
        self.configure_sweep_linear(start, stop, steps, source, delay)
        return self.execute_sweep()
