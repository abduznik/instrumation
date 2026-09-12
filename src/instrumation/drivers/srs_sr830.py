from .base import LockInAmplifier
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("LOCKIN")
class SRSSR830(RealDriver, LockInAmplifier):
    """Driver for Stanford Research Systems SR830 DSP Lock-In Amplifier.

    Like the SRS DS345, uses terse colon-free command mnemonics
    (``FREQ``, ``PHAS``, ``SLVL``, ``SENS``, ``OFLT``, ``HARM``)
    rather than a SCPI ``:SOURce:*``/``:SENSe:*`` subtree. ``SENSe``
    and time-constant values are indexed by integer code (see the
    SR830 manual's sensitivity/time-constant tables), not physical
    units directly -- ``set_sensitivity()``/``set_time_constant()``
    accept a physical value and round it to the nearest supported
    code. ``SNAP?`` reads multiple parameters (X, Y, R, theta, aux
    inputs, reference frequency) at a single instant, avoiding the
    time skew that separate ``OUTP?`` queries would introduce.

    Command Reference (SR830 Manual):
        - FREQ f     — sets/queries reference frequency (internal osc.)
        - PHAS x     — sets/queries reference phase shift (degrees)
        - SLVL x     — sets/queries sine output amplitude (0.004-5.000 V)
        - HARM i     — sets/queries detection harmonic (1-19999)
        - SENS i     — sets/queries sensitivity by index (0-26)
        - OFLT i     — sets/queries time constant by index (0-19)
        - OUTP? i    — reads X(1)/Y(2)/R(3)/theta(4)
        - SNAP? i,j{,k,l,m,n}  — simultaneous multi-parameter read
    """

    _SENS_TABLE = [
        2e-9, 5e-9, 10e-9, 20e-9, 50e-9, 100e-9, 200e-9, 500e-9,
        1e-6, 2e-6, 5e-6, 10e-6, 20e-6, 50e-6, 100e-6, 200e-6, 500e-6,
        1e-3, 2e-3, 5e-3, 10e-3, 20e-3, 50e-3, 100e-3, 200e-3, 500e-3, 1.0,
    ]
    _OFLT_TABLE = [
        10e-6, 30e-6, 100e-6, 300e-6, 1e-3, 3e-3, 10e-3, 30e-3, 100e-3,
        300e-3, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1e3, 3e3, 10e3, 30e3,
    ]

    def preset(self, automation_optimized: bool = True) -> None:
        self.write("*RST")
        self.wait_ready()

    def set_reference_frequency(self, hz: float) -> None:
        self.write(f"FREQ {hz}")

    def get_reference_frequency(self) -> float:
        return float(self.query("FREQ?"))

    def set_reference_phase(self, degrees: float) -> None:
        self.write(f"PHAS {degrees}")

    def get_reference_phase(self) -> float:
        return float(self.query("PHAS?"))

    def set_sine_output_amplitude(self, volts: float) -> None:
        self.write(f"SLVL {volts}")

    def set_harmonic(self, n: int) -> None:
        self.write(f"HARM {n}")

    def set_sensitivity(self, volts_or_amps: float) -> None:
        index = min(range(len(self._SENS_TABLE)),
                    key=lambda i: abs(self._SENS_TABLE[i] - volts_or_amps))
        self.write(f"SENS {index}")

    def set_time_constant(self, seconds: float) -> None:
        index = min(range(len(self._OFLT_TABLE)),
                     key=lambda i: abs(self._OFLT_TABLE[i] - seconds))
        self.write(f"OFLT {index}")

    def measure_xy(self) -> MeasurementResult:
        resp = self.query("SNAP?1,2")
        x, y = (float(v) for v in resp.split(","))
        return MeasurementResult((x, y), "V")

    def measure_r_theta(self) -> MeasurementResult:
        resp = self.query("SNAP?3,4")
        r, theta = (float(v) for v in resp.split(","))
        return MeasurementResult((r, theta), "V,deg")

    def auto_gain(self) -> None:
        self.write("AGAN")

    def auto_phase(self) -> None:
        self.write("APHS")

    def measure_frequency(self) -> MeasurementResult:
        return MeasurementResult(self.get_reference_frequency(), "Hz")

    def shutdown_safety(self) -> None:
        self.set_sine_output_amplitude(0.004)
        self.sync_config()
