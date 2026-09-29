from .base import TemperatureController
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("TEMP")
class LakeShore336(RealDriver, TemperatureController):
    """Driver for Lake Shore Model 336 Cryogenic Temperature Controller.

    Validated Model: 336 (4 sensor inputs A-D, 2 PID control loops).
    The 335 (2 inputs/1 loop) shares the same ASCII mnemonic command set
    and should also work against this driver.

    IEEE-488.2-style ASCII mnemonic SCPI-like command set over GPIB, USB,
    or Ethernet (all three interfaces are equally capable). Every
    remote-operation function documented in the Model 336 User's Manual
    is reachable via these commands; unlike a bench PSU, there is no
    single voltage/current source -- sensor inputs are lettered
    (A, B, C, D) and control loops are numbered (1, 2).

    Command Reference (Lake Shore Model 336 User's Manual):
        - KRDG? <input>              — kelvin reading for input A-D
        - CRDG? <input>              — Celsius reading for input A-D
        - SRDG? <input>              — sensor-units reading for input A-D
        - INTYPE <input>,<params>    — sensor input type/range/curve config
        - INTYPE? <input>            — query sensor input type config
        - SETP <loop>,<value>        — control loop setpoint (Kelvin)
        - SETP? <loop>               — query control loop setpoint
        - PID <loop>,<P>,<I>,<D>     — set PID gains for a loop
        - PID? <loop>                — query PID gains
        - RANGE <loop>,<range>       — heater range (0=Off,1=Low,2=Med,3=High)
        - RANGE? <loop>              — query heater range
        - HTR? <loop>                — heater output (% of current range)
        - RAMP <loop>,<onoff>,<rate> — setpoint ramp rate (K/min) enable
        - RAMP? <loop>               — query ramp configuration
        - OUTMODE <loop>,<mode>,<in>,<pwr> — output mode / input assignment
                           (0=Off, 1=Closed Loop PID, 2=Zone, 3=Open Loop)
        - ATUNE <loop>,<mode>        — start autotune (0=P,1=P and I,2=P,I,D)
        - ALARMST? <input>           — alarm status for an input
        - *IDN? / *RST / *CLS / *OPC?
    """

    _RANGE_MAP = {"OFF": 0, "LOW": 1, "MEDIUM": 2, "MED": 2, "HIGH": 3}
    _RANGE_MAP_REV = {0: "OFF", 1: "LOW", 2: "MEDIUM", 3: "HIGH"}
    # Model 336 User's Manual, OUTMODE <output>,<mode>,<input>,<powerup enable>
    _CONTROL_MODES = {"OFF": 0, "PID": 1, "CLOSEDLOOP": 1, "ZONE": 2,
                      "OPENLOOP": 3, "MANUAL": 3}

    def get_temperature(self, input_channel: str) -> MeasurementResult:
        val = self.query_ascii(f"KRDG? {input_channel.upper()}")
        return MeasurementResult(float(val), "K", channel=input_channel.upper())

    def get_temperature_celsius(self, input_channel: str) -> MeasurementResult:
        """Returns the Celsius reading for the given sensor input (CRDG?)."""
        val = self.query_ascii(f"CRDG? {input_channel.upper()}")
        return MeasurementResult(float(val), "C", channel=input_channel.upper())

    def get_sensor_reading(self, input_channel: str) -> MeasurementResult:
        """Returns the raw sensor-units reading (Ohms/mV/etc.) for an input (SRDG?)."""
        val = self.query_ascii(f"SRDG? {input_channel.upper()}")
        return MeasurementResult(float(val), "sensor-units", channel=input_channel.upper())

    def set_setpoint(self, loop: int, temperature: float) -> None:
        self.safe_send(f"SETP {loop},{temperature}")

    def get_setpoint(self, loop: int) -> float:
        return float(self.query_ascii(f"SETP? {loop}"))

    def set_pid(self, loop: int, p: float, i: float, d: float) -> None:
        self.safe_send(f"PID {loop},{p},{i},{d}")

    def get_pid(self, loop: int) -> tuple:
        resp = self.query_ascii(f"PID? {loop}")
        parts = [float(x) for x in resp.split(",")]
        return tuple(parts[:3]) if len(parts) >= 3 else (0.0, 0.0, 0.0)

    def set_heater_range(self, loop: int, range_setting: str) -> None:
        key = range_setting.upper()
        if key not in self._RANGE_MAP:
            raise ValueError(f"Invalid heater range: {range_setting}")
        self.safe_send(f"RANGE {loop},{self._RANGE_MAP[key]}")

    def get_heater_range(self, loop: int) -> str:
        code = int(self.query_ascii(f"RANGE? {loop}"))
        return self._RANGE_MAP_REV.get(code, "OFF")

    def get_heater_output(self, loop: int) -> MeasurementResult:
        val = self.query_ascii(f"HTR? {loop}")
        return MeasurementResult(float(val), "%", channel=f"LOOP{loop}")

    def set_ramp_rate(self, loop: int, rate_k_per_min: float, state: bool = True) -> None:
        self.safe_send(f"RAMP {loop},{1 if state else 0},{rate_k_per_min}")

    def get_ramp_rate(self, loop: int) -> tuple:
        """Returns (enabled, rate_k_per_min) for the given loop's ramp config (RAMP?)."""
        resp = self.query_ascii(f"RAMP? {loop}")
        parts = resp.split(",")
        enabled = parts[0].strip() in ("1", "ON")
        rate = float(parts[1]) if len(parts) > 1 else 0.0
        return (enabled, rate)

    def set_sensor_type(self, input_channel: str, sensor_type: str) -> None:
        """Configures a sensor input type (INTYPE <input>,<type params>).

        `sensor_type` is passed through verbatim as the comma-separated
        INTYPE parameter list (sensor type, autorange, range, compensation,
        units), since the exact field encoding is model/firmware specific.
        """
        self.safe_send(f"INTYPE {input_channel.upper()},{sensor_type}")

    def get_sensor_type(self, input_channel: str) -> str:
        return self.query_ascii(f"INTYPE? {input_channel.upper()}").strip()

    def set_control_mode(self, loop: int, mode: str) -> None:
        """Selects the loop control mode (OUTMODE).

        `OUTMODE` takes four parameters, so the output's current control input
        and powerup-enable settings are read back with `OUTMODE?` and preserved.
        """
        key = mode.upper()
        if key not in self._CONTROL_MODES:
            raise ValueError(f"Invalid control mode: {mode}")
        parts = [p.strip() for p in self.query_ascii(f"OUTMODE? {loop}").split(",")]
        if len(parts) < 3:
            raise ValueError(f"Unexpected OUTMODE? response: {parts!r}")
        in_ch, powerup = parts[1], parts[2]
        self.safe_send(f"OUTMODE {loop},{self._CONTROL_MODES[key]},{in_ch},{powerup}")

    def autotune(self, loop: int, mode: str = "PI") -> None:
        modes = {"P": 0, "PI": 1, "PID": 2}
        key = mode.upper()
        if key not in modes:
            raise ValueError(f"Invalid autotune mode: {mode}")
        self.write(f"ATUNE {loop},{modes[key]}")

    def get_alarm_status(self, input_channel: str) -> str:
        return self.query_ascii(f"ALARMST? {input_channel.upper()}").strip()

    def shutdown_safety(self) -> None:
        # Force both loops' heater outputs off -- the closest equivalent to
        # a PSU's "outputs off" for a temperature controller.
        self.set_heater_range(1, "OFF")
        self.set_heater_range(2, "OFF")
        self.sync_config()
