from abc import ABC, abstractmethod
from typing import List, Union, Dict, Any, Optional
import asyncio
import functools
import logging

from ..results import MeasurementResult
from ..exceptions import OverloadError, ConfigurationError

logger = logging.getLogger(__name__)


def _unsupported(fn):
    """Marks a base-class default as 'feature not supported'.

    The wrapped default logs a warning via ``_unsupported_feature`` and then
    returns the placeholder value of ``fn``. ``InstrumentDriver.supports``
    reports False for any method still carrying this marker.
    """
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        self._unsupported_feature(fn.__name__)
        return fn(self, *args, **kwargs)
    wrapper._unsupported = True
    return wrapper

class InstrumentDriver(ABC):
    """Abstract Base Class for all instrument drivers following the 'Abstract Hardware' spec."""

    # Explicit simulated-driver marker (GH #160). Simulated/digital-twin
    # driver classes set this True; real drivers leave it False. Factory
    # filtering MUST use this flag instead of string-matching class names.
    is_simulated = False

    def __init__(self, resource: str) -> None:
        self.resource = resource
        self.connected = False
        # Instance flag mirrors the class-level simulated marker so both
        # class- and instance-level checks agree (GH #160).
        self.is_simulated = type(self).is_simulated
        
        # Identity & Capabilities
        self.identity: Dict[str, str] = {"manufacturer": "", "model": "", "serial": "", "version": ""}
        self.options: List[str] = []
        self.error_stack: List[str] = []
        
        # Software Safety Guardrails
        self.min_frequency = 0.0
        self.max_frequency = 1e12
        self.max_power_dbm = 0.0
        self.max_voltage = 0.0

    def __getattr__(self, name: str) -> Any:
        """Dynamic async wrapper for all driver methods."""
        if name.startswith("async_"):
            sync_name = name[6:]
            if sync_name and hasattr(self, sync_name):
                sync_method = getattr(self, sync_name)
                if not callable(sync_method):
                    raise AttributeError(
                        f"'{self.__class__.__name__}' has no async counterpart "
                        f"for non-callable attribute '{sync_name}'"
                    )
                async def wrapper(*args: Any, **kwargs: Any) -> Any:
                    return await asyncio.to_thread(sync_method, *args, **kwargs)
                return wrapper
            # Likely typo'd async_ name: the sync attribute doesn't exist.
            raise AttributeError(
                f"'{self.__class__.__name__}' has no attribute '{sync_name}' "
                f"(resolved from async_{sync_name}); did you mean "
                f"'async_{name[6:]}' on the sync driver?"
            )
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


    @property
    def resource_address(self) -> str:
        return self.resource

    @abstractmethod
    def connect(self) -> None:
        """Establishes connection and performs identity/option discovery."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Safely tears down connection."""
        pass

    def close(self) -> None:
        self.disconnect()

    @abstractmethod
    def write(self, command: str) -> None: pass

    @abstractmethod
    def query(self, command: str) -> str: pass

    @abstractmethod
    def safe_send(self, command: str) -> None:
        """Sends command and immediately checks SYST:ERR?."""
        raise NotImplementedError()

    @abstractmethod
    def query_ascii(self, command: str) -> str:
        """Sends command, reads response, and checks for errors."""
        raise NotImplementedError()

    @abstractmethod
    def query_binary_values(self, command: str, datatype: str = 'f', is_big_endian: bool = False) -> List[float]:
        """High-speed binary data transfer."""
        raise NotImplementedError()

    @abstractmethod
    def get_id(self) -> str: pass

    # --- Global Logic & Synchronization ---
    @abstractmethod
    def preset(self, automation_optimized: bool = True) -> None: pass

    @abstractmethod
    def clear_status(self) -> None:
        """Executes *CLS."""
        pass

    @abstractmethod
    def sync_config(self) -> None:
        """Executes *CLS and *WAI for a clean slate."""
        pass

    @abstractmethod
    def wait_ready(self, timeout: float = 30.0) -> None:
        """Standard polling loop for *OPC?."""
        pass

    @abstractmethod
    def shutdown_safety(self) -> None:
        """Emergency shutdown protocol (Outputs OFF, Power/Volt 0)."""
        pass

    @abstractmethod
    def check_errors(self) -> None:
        """Queries SYST:ERR? and updates local error_stack."""
        pass

    @_unsupported
    def save_state(self, index: Union[int, str]) -> None:
        """Saves current state to memory."""

    @_unsupported
    def load_state(self, index: Union[int, str]) -> None:
        """Recalls state from memory."""

    # --- Unit Guards & Formatting ---
    def format_frequency(self, val: Union[float, str]) -> str:
        """Ensures input is Hz and formats for SCPI (e.g. 1.5e9 -> '1.5 GHz')."""
        hz = float(val)
        self._validate_frequency(hz)
        if hz >= 1e9:
            return f"{hz/1e9:.6f} GHz"
        if hz >= 1e6:
            return f"{hz/1e6:.6f} MHz"
        if hz >= 1e3:
            return f"{hz/1e3:.6f} kHz"
        return f"{hz:.0f} Hz"

    def format_power(self, dbm: float) -> str:
        self._validate_power(dbm)
        return f"{dbm:.2f} DBM"

    def _unsupported_feature(self, feature_name: str) -> None:
        model = self.identity.get("model") or "Instrument"
        logger.warning(
            "Feature '%s' is not supported by %s", feature_name, model
        )

    def _validate_frequency(self, hz: float) -> None:
        if hz < self.min_frequency or hz > self.max_frequency:
            raise ConfigurationError(f"Frequency {hz} Hz out of safety range")

    def _validate_power(self, dbm: float) -> None:
        if dbm > self.max_power_dbm:
            raise OverloadError(f"Power {dbm} dBm exceeds safety limit")

    def supports(self, feature: str) -> bool:
        """True if this driver implements ``feature`` (a method name).

        A method counts as unsupported when the driver inherits the
        library's generic ``_unsupported_feature`` default for it.
        """
        method = getattr(type(self), feature, None)
        return callable(method) and not getattr(method, "_unsupported", False)

    # --- Measurements (optional; Oscilloscope / FrequencyCounter make them required) ---
    @_unsupported
    def measure_frequency(self) -> MeasurementResult:
        return MeasurementResult(0.0, "Hz")

    @_unsupported
    def measure_duty_cycle(self) -> MeasurementResult:
        return MeasurementResult(0.0, "%")

    @_unsupported
    def measure_v_peak_to_peak(self) -> MeasurementResult:
        return MeasurementResult(0.0, "V")

    def __enter__(self) -> "InstrumentDriver":
        self.connect()
        return self

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Any) -> None:
        try:
            self.shutdown_safety()
        except Exception:
            pass
        self.disconnect()

class ElectronicLoad(InstrumentDriver):
    @abstractmethod
    def set_mode(self, mode: str) -> None:
        """Sets the operating mode, typically CC, CV, CR, or CP."""
        pass

    @abstractmethod
    def get_mode(self) -> str:
        """Returns the active operating mode."""
        pass

    @abstractmethod
    def set_current(self, amps: float) -> None:
        """Sets the constant current value in CC mode."""
        pass

    @abstractmethod
    def get_current(self) -> float:
        """Returns the set current value in CC mode."""
        pass

    @abstractmethod
    def set_voltage(self, volts: float) -> None:
        """Sets the constant voltage value in CV mode."""
        pass

    @abstractmethod
    def get_voltage(self) -> float:
        """Returns the set voltage value in CV mode."""
        pass

    @abstractmethod
    def set_resistance(self, ohms: float) -> None:
        """Sets the constant resistance value in CR mode."""
        pass

    @abstractmethod
    def get_resistance(self) -> float:
        """Returns the set resistance value in CR mode."""
        pass

    @abstractmethod
    def set_power(self, watts: float) -> None:
        """Sets the constant power value in CP mode."""
        pass

    @abstractmethod
    def get_power(self) -> float:
        """Returns the set power value in CP mode."""
        pass

    @abstractmethod
    def set_input(self, state: bool) -> None:
        """Turns the load input ON (True) or OFF (False)."""
        pass

    @abstractmethod
    def get_input(self) -> bool:
        """Returns the input state (ON/OFF)."""
        pass

    @abstractmethod
    def measure_voltage(self) -> MeasurementResult:
        """Measures the actual input voltage at the load terminals."""
        pass

    @abstractmethod
    def measure_current(self) -> MeasurementResult:
        """Measures the actual current being drawn by the load."""
        pass

    @abstractmethod
    def measure_power(self) -> MeasurementResult:
        """Measures the actual power being consumed by the load."""
        pass

    @_unsupported
    def set_ovp(self, voltage: float) -> None:
        """Sets the over-voltage protection limit."""
        pass

    @_unsupported
    def set_ocp(self, current: float) -> None:
        """Sets the over-current protection limit."""
        pass

    @_unsupported
    def set_opp(self, power: float) -> None:
        """Sets the over-power protection limit."""
        pass

    @_unsupported
    def clear_protection(self) -> None:
        """Clears any tripped protection status."""
        pass

class FrequencyCounter(InstrumentDriver):
    """Abstract Base for Frequency Counters / Timer/Counter instruments."""

    @abstractmethod
    def measure_frequency(self, range: str = "AUTO") -> MeasurementResult:
        """Measures frequency. Range can be 'AUTO' or a specific range in Hz."""
        pass

    @abstractmethod
    def measure_period(self, range: str = "AUTO") -> MeasurementResult:
        """Measures period. Range can be 'AUTO' or a specific range in seconds."""
        pass

    @abstractmethod
    def measure_time_interval(self, start_trigger: str, stop_trigger: str) -> MeasurementResult:
        """Measures time interval between two events (e.g. 'CH1', 'CH2')."""
        pass

    @abstractmethod
    def set_impedance(self, ohms: float) -> None:
        """Sets input impedance (50 or 1e6)."""
        pass

    @abstractmethod
    def set_trigger_level(self, volts: float) -> None:
        """Sets the trigger level voltage."""
        pass

    @abstractmethod
    def set_coupling(self, dc_ac: str) -> None:
        """Sets input coupling — 'DC' or 'AC'."""
        pass

    @abstractmethod
    def set_auto_range(self, state: bool) -> None:
        """Enables or disables auto-ranging."""
        pass

class LCRMeter(InstrumentDriver):
    """Abstract Base for LCR Meters / Impedance Analyzers."""

    @abstractmethod
    def set_frequency(self, hz: float) -> None:
        """Sets the test signal frequency."""
        pass

    @abstractmethod
    def get_frequency(self) -> float:
        """Returns the test signal frequency."""
        pass

    @abstractmethod
    def set_voltage_level(self, volts: float) -> None:
        """Sets the AC test signal voltage level."""
        pass

    @abstractmethod
    def set_measurement_function(self, function: str) -> None:
        """Sets the impedance parameter type, e.g. 'CPD', 'CSD', 'LSD', 'RX'."""
        pass

    @abstractmethod
    def get_measurement_function(self) -> str:
        """Returns the active impedance parameter type."""
        pass

    @abstractmethod
    def measure(self) -> MeasurementResult:
        """Triggers and fetches the primary/secondary measurement pair.

        Returns a MeasurementResult whose value is a (primary, secondary)
        tuple, e.g. (capacitance, dissipation_factor) for CPD.
        """
        pass

    @_unsupported
    def set_bias_voltage(self, volts: float) -> None:
        """Sets the DC bias voltage level (if supported)."""

    @_unsupported
    def set_bias_state(self, state: bool) -> None:
        """Enables/disables the DC bias output (if supported)."""

    @_unsupported
    def set_auto_range(self, state: bool) -> None:
        """Enables or disables auto-ranging."""

class LockInAmplifier(InstrumentDriver):
    """Abstract Base for Lock-In Amplifiers."""

    @abstractmethod
    def set_reference_frequency(self, hz: float) -> None:
        """Sets the internal oscillator reference frequency."""
        pass

    @abstractmethod
    def get_reference_frequency(self) -> float:
        """Returns the reference frequency (internal or external)."""
        pass

    @abstractmethod
    def set_reference_phase(self, degrees: float) -> None:
        """Sets the reference phase shift."""
        pass

    @abstractmethod
    def set_sine_output_amplitude(self, volts: float) -> None:
        """Sets the internal oscillator sine output amplitude."""
        pass

    @abstractmethod
    def set_time_constant(self, seconds: float) -> None:
        """Sets the low-pass filter time constant."""
        pass

    @abstractmethod
    def set_sensitivity(self, volts_or_amps: float) -> None:
        """Sets the input full-scale sensitivity."""
        pass

    @abstractmethod
    def measure_xy(self) -> MeasurementResult:
        """Returns a simultaneous (X, Y) reading as a MeasurementResult."""
        pass

    @abstractmethod
    def measure_r_theta(self) -> MeasurementResult:
        """Returns a simultaneous (R, theta) reading as a MeasurementResult."""
        pass

    @_unsupported
    def set_harmonic(self, n: int) -> None:
        """Sets the detection harmonic (default 1st harmonic)."""

    @_unsupported
    def auto_gain(self) -> None:
        """Triggers an auto-gain/auto-sensitivity routine."""

    @_unsupported
    def auto_phase(self) -> None:
        """Triggers an auto-phase routine."""

    def measure_frequency(self) -> MeasurementResult:
        return MeasurementResult(self.get_reference_frequency(), "Hz")

class Multimeter(InstrumentDriver):
    @abstractmethod
    def configure_voltage_dc(self) -> None: pass
    @abstractmethod
    def configure_voltage_ac(self) -> None: pass
    @abstractmethod
    def measure_voltage(self, ac: bool = False) -> MeasurementResult: pass
    @abstractmethod
    def measure_resistance(self, four_wire: bool = False) -> MeasurementResult: pass
    @abstractmethod
    def measure_current(self, ac: bool = False) -> MeasurementResult: pass
    @abstractmethod
    def set_auto_range(self, state: bool) -> None: pass

class PowerSupply(InstrumentDriver):
    @abstractmethod
    def set_voltage(self, voltage: float) -> None: pass
    @abstractmethod
    def get_voltage(self) -> float: pass
    @abstractmethod
    def set_current_limit(self, current: float) -> None: pass
    def set_current(self, current: float) -> None:
        """Generalized alias for set_current_limit."""
        self.set_current_limit(current)
    @abstractmethod
    def get_current(self) -> MeasurementResult: pass
    @abstractmethod
    def set_output(self, state: bool) -> None: pass
    @abstractmethod
    def get_output(self) -> bool: pass
    @_unsupported
    def set_ovp(self, voltage: float) -> None: pass
    @_unsupported
    def set_ocp(self, current: float) -> None: pass
    @abstractmethod
    def measure_voltage_actual(self) -> MeasurementResult: pass
    @abstractmethod
    def measure_current(self) -> MeasurementResult: pass

    def set_voltage_limit(self, voltage: float) -> None:
        """Generalized alias for Over-Voltage Protection (OVP)."""
        self.set_ovp(voltage)

    def measure_voltage(self) -> MeasurementResult:
        """Generalized alias for measure_voltage_actual."""
        return self.measure_voltage_actual()

    @_unsupported
    def clear_protection(self) -> None: pass

    @_unsupported
    def measure_power(self) -> MeasurementResult:
        """Queries the actual measured output power (Watts)."""
        return MeasurementResult(0.0, "W")

    @_unsupported
    def set_foldback_mode(self, mode: str) -> None:
        """Sets the foldback protection mode (OFF, CC, or CV)."""

    @_unsupported
    def set_foldback_delay(self, seconds: float) -> None:
        """Sets the delay for foldback protection."""

    @_unsupported
    def set_autostart(self, state: bool) -> None:
        """Sets the Power-ON state (SAFE/OFF or AUTO/ON)."""

    @_unsupported
    def get_mode(self) -> str:
        """Returns the current operation mode (CV, CC, or OFF)."""
        return "OFF"

class SpectrumAnalyzer(InstrumentDriver):
    @abstractmethod
    def peak_search(self) -> None: pass
    @abstractmethod
    def get_marker_amplitude(self) -> MeasurementResult: pass
    @abstractmethod
    def set_center_freq(self, hz: float) -> None: pass
    @abstractmethod
    def get_center_freq(self) -> float: pass
    @abstractmethod
    def set_span(self, hz: float) -> None: pass
    @abstractmethod
    def get_span(self) -> float: pass
    @abstractmethod
    def set_rbw(self, hz: float) -> None: pass
    @abstractmethod
    def set_vbw(self, hz: float) -> None: pass
    @abstractmethod
    def get_trace_data(self) -> MeasurementResult: pass

    def get_peak_value(self) -> MeasurementResult:
        """Helper: Performs peak search and returns marker amplitude."""
        self.peak_search()
        return self.get_marker_amplitude()

class NetworkAnalyzer(InstrumentDriver):
    @abstractmethod
    def set_start_frequency(self, freq_hz: float) -> None: pass
    @abstractmethod
    def set_stop_frequency(self, freq_hz: float) -> None: pass
    
    @_unsupported
    def set_center_freq(self, freq_hz: float) -> None: 
        pass

    def set_center_frequency(self, freq_hz: float) -> None:
        """Alias for set_center_freq."""
        self.set_center_freq(freq_hz)
    
    @_unsupported
    def set_span(self, span_hz: float) -> None: 
        pass
    
    @abstractmethod
    def set_points(self, num_points: int) -> None: pass
    
    @_unsupported
    def set_if_bandwidth(self, hz: float) -> None: 
        pass
    
    @_unsupported
    def set_power_level(self, dbm: float) -> None: 
        pass
    
    @_unsupported
    def set_sweep_type(self, sweep_type: str) -> None: 
        pass
    
    @_unsupported
    def set_averaging(self, state: bool, count: int = 10) -> None: 
        pass
    
    @_unsupported
    def set_continuous(self, state: bool) -> None: 
        pass
    
    @abstractmethod
    def set_parameter(self, parameter: str) -> None: pass  # e.g., "S11", "S21"
    
    @abstractmethod
    def get_trace_data(self, measurement_name: str = "CH1_S11_1") -> MeasurementResult: pass
    
    @abstractmethod
    def get_complex_trace(self, measurement_name: str = "CH1_S11_1") -> MeasurementResult: pass
    
    @_unsupported
    def get_smith_data(self, measurement_name: str = "CH1_S11_1") -> MeasurementResult:
        return MeasurementResult([], "Z")
    
    @_unsupported
    def peak_search(self, marker: int = 1) -> None: 
        pass
    
    @_unsupported
    def get_marker_x(self, marker: int = 1) -> float: 
        return 0.0
    
    @_unsupported
    def get_marker_y(self, marker: int = 1) -> float: 
        return 0.0
    
    @_unsupported
    def save_state(self, filename: str) -> None: 
        pass
    
    @_unsupported
    def load_state(self, filename: str) -> None: 
        pass

    @_unsupported
    def wait_for_sweep(self) -> None:
        """Wait for the current sweep to complete."""

class Oscilloscope(InstrumentDriver):
    @abstractmethod
    def run(self) -> None: pass
    @abstractmethod
    def stop(self) -> None: pass
    @abstractmethod
    def single(self) -> None: pass
    @abstractmethod
    def get_waveform(self, channel: int) -> MeasurementResult: pass
    @abstractmethod
    def auto_scale(self) -> None: pass
    @abstractmethod
    def set_trigger(self, source: str, level: float, slope: str) -> None: pass
    @abstractmethod
    def get_screenshot(self) -> bytes: pass
    @abstractmethod
    def measure_frequency(self, channel: int = 1) -> MeasurementResult: pass
    @abstractmethod
    def measure_duty_cycle(self, channel: int = 1) -> MeasurementResult: pass
    @abstractmethod
    def measure_v_peak_to_peak(self, channel: int = 1) -> MeasurementResult: pass

class SignalGenerator(InstrumentDriver):
    @abstractmethod
    def set_frequency(self, hz: float) -> None: pass
    @abstractmethod
    def set_amplitude(self, dbm: float) -> None: pass
    @abstractmethod
    def set_output(self, state: bool) -> None: pass
    @abstractmethod
    def set_mod_state(self, mod_type: str, state: bool) -> None: pass
    @abstractmethod
    def start_sweep(self, start: float, stop: float, points: int, dwell: float) -> None: pass
    @_unsupported
    def configure_list_sweep(self, freq_list: List[float], power_list: List[float]) -> None: pass
    @abstractmethod
    def set_reference_clock(self, source: str) -> None: pass

class FunctionGenerator(SignalGenerator):
    """Specific for AFGs which use Volts/Waveforms instead of just dBm."""
    @abstractmethod
    def set_voltage(self, vpp: float) -> None: pass
    @abstractmethod
    def set_offset(self, volts: float) -> None: pass
    @abstractmethod
    def set_waveform(self, shape: str) -> None: pass # SIN, SQU, PULS, RAMP, NOIS, DC

class ACPowerSource(InstrumentDriver):
    """Abstract Base for Programmable AC Power Sources.

    Every `PowerSupply` driver in this library is DC-only -- a single
    voltage/current setpoint with no frequency, phase, or output-mode
    concept. An AC source needs frequency programming and an
    AC/DC/AC+DC output mode, plus true-RMS AC measurement, none of
    which fits the `PowerSupply` ABC cleanly.
    """

    @abstractmethod
    def set_voltage(self, volts_rms: float) -> None:
        """Sets the AC output voltage setpoint (Volts RMS)."""
        pass

    @abstractmethod
    def get_voltage(self) -> float:
        """Returns the AC output voltage setpoint (Volts RMS)."""
        pass

    @abstractmethod
    def set_frequency(self, hz: float) -> None:
        """Sets the output frequency (Hz)."""
        pass

    @abstractmethod
    def get_frequency(self) -> float:
        """Returns the output frequency (Hz)."""
        pass

    @abstractmethod
    def set_output_mode(self, mode: str) -> None:
        """Sets the output mode: 'AC', 'DC', or 'AC+DC'."""
        pass

    @abstractmethod
    def get_output_mode(self) -> str:
        """Returns the active output mode."""
        pass

    @abstractmethod
    def set_output(self, state: bool) -> None:
        """Turns the AC output ON (True) or OFF (False)."""
        pass

    @abstractmethod
    def get_output(self) -> bool:
        """Returns the output enable state."""
        pass

    @abstractmethod
    def measure_voltage(self) -> MeasurementResult:
        """Measures the actual output voltage (true-RMS)."""
        pass

    @abstractmethod
    def measure_current(self) -> MeasurementResult:
        """Measures the actual output current (true-RMS)."""
        pass

    @abstractmethod
    def measure_power(self) -> MeasurementResult:
        """Measures the actual real output power (Watts)."""
        pass

    @abstractmethod
    def set_current_limit(self, amps_rms: float) -> None:
        """Sets the output current limit (Amps RMS)."""
        pass

    @_unsupported
    def set_ovp(self, volts: float) -> None:
        """Sets the over-voltage protection trip point."""
        pass

    @_unsupported
    def set_ocp(self, amps: float) -> None:
        """Sets the over-current protection trip point."""
        pass

    @_unsupported
    def clear_protection(self) -> None:
        """Clears any tripped protection status."""
        pass

    @_unsupported
    def set_dc_offset(self, volts: float) -> None:
        """Sets the DC offset voltage (used in 'AC+DC' output mode)."""

    @_unsupported
    def set_voltage_range(self, range_name: str) -> None:
        """Selects a fixed voltage range, e.g. 'LOW'/'HIGH' (if supported)."""

    def measure_frequency(self) -> MeasurementResult:
        return MeasurementResult(self.get_frequency() if hasattr(self, "get_frequency") else 0.0, "Hz")

class DataAcquisitionUnit(InstrumentDriver):
    """Abstract Base for Data Acquisition / Switch Units (DAQ + relay mux).

    Unlike a `Multimeter`, a DAQ/switch unit multiplexes many channels
    through plug-in modules (relay multiplexers, matrix switches,
    digital I/O, totalizers) behind a single measurement engine.
    Channels/slots are addressed with SCPI channel-list syntax, e.g.
    ``(@101,102,203)`` -- slot 1 channels 01/02, slot 2 channel 03.
    """

    @staticmethod
    def format_channel_list(channels: Union[List[int], List[str], str]) -> str:
        """Builds a SCPI channel-list string, e.g. ``(@101,102,203)``.

        Accepts a pre-formatted string (returned as-is if it already
        starts with ``(@``), or a list of channel numbers/strings that
        gets comma-joined and wrapped.
        """
        if isinstance(channels, str):
            return channels if channels.startswith("(@") else f"(@{channels})"
        return f"(@{','.join(str(c) for c in channels)})"

    @abstractmethod
    def configure_channel(self, channel: str, function: str, **kwargs: Any) -> None:
        """Configures the measurement function for a channel or channel list.

        `function` is a measurement function mnemonic, e.g. 'VOLT:DC',
        'VOLT:AC', 'RES', 'FRES' (4-wire), 'TEMP', 'FREQ'.
        """
        pass

    @abstractmethod
    def measure_scan(self, channels: Union[List[int], List[str], str]) -> MeasurementResult:
        """Configures a scan list and returns one reading per channel."""
        pass

    @abstractmethod
    def read_channel(self, channel: str) -> MeasurementResult:
        """Immediately measures and returns a single channel's reading."""
        pass

    @abstractmethod
    def close_relay(self, channel: str) -> None:
        """Closes (activates) the relay for the given channel/channel list."""
        pass

    @abstractmethod
    def open_relay(self, channel: str) -> None:
        """Opens (deactivates) the relay for the given channel/channel list."""
        pass

    @abstractmethod
    def get_relay_state(self, channel: str) -> bool:
        """Returns True if the given channel's relay is closed."""
        pass

    @_unsupported
    def set_scan_list(self, channels: Union[List[int], List[str], str]) -> None:
        """Defines the scan list used by a subsequent triggered scan."""

    @_unsupported
    def start_scan(self) -> None:
        """Initiates a scan over the configured scan list."""

    @_unsupported
    def get_scan_data(self) -> MeasurementResult:
        """Fetches the results of the most recent scan."""
        return MeasurementResult([], "")

    @_unsupported
    def set_trigger_source(self, source: str) -> None:
        """Sets the scan trigger source, e.g. 'IMMEDIATE', 'BUS', 'EXTERNAL'."""

class PowerMeter(InstrumentDriver):
    """Abstract Base for RF Power Meters (CW and peak/pulse).

    Distinct from a bench `PowerSupply`: a power meter is a measurement
    instrument only, reading RF power from an external sensor rather
    than sourcing voltage/current. Covers both CW average-power meters
    and wideband peak/pulse power meters (e.g. Boonton 4530 Series).
    """

    @abstractmethod
    def measure_power(self) -> MeasurementResult:
        """Measures the current (CW average) RF power reading."""
        pass

    @abstractmethod
    def set_frequency(self, hz: float) -> None:
        """Sets the CW frequency used for the sensor's cal-factor lookup."""
        pass

    @abstractmethod
    def get_frequency(self) -> float:
        """Returns the configured CW frequency."""
        pass

    @abstractmethod
    def set_power_unit(self, unit: str) -> None:
        """Sets the readout unit, e.g. 'DBM' or 'W'."""
        pass

    @abstractmethod
    def set_offset(self, db: float) -> None:
        """Sets a relative gain/loss offset applied to the reading (dB)."""
        pass

    @_unsupported
    def measure_peak_power(self) -> MeasurementResult:
        """Measures the peak (pulse) RF power reading, if supported."""
        return MeasurementResult(0.0, "dBm")

    @_unsupported
    def set_video_bandwidth(self, hz: float) -> None:
        """Sets the video bandwidth used for pulse/peak demodulation."""

    @_unsupported
    def set_trigger_source(self, source: str) -> None:
        """Sets the trigger source, e.g. 'INTERNAL', 'EXTERNAL', 'FREE_RUN'."""

    @_unsupported
    def set_trigger_level(self, dbm: float) -> None:
        """Sets the trigger level for peak/pulse capture (dBm)."""

    @_unsupported
    def measure_pulse_width(self) -> MeasurementResult:
        """Measures the pulse width of the last captured pulse, if supported."""
        return MeasurementResult(0.0, "s")

    @_unsupported
    def zero(self) -> None:
        """Performs a sensor zero calibration."""

class TemperatureController(InstrumentDriver):
    """Abstract Base for Cryogenic/Process Temperature Controllers.

    Unlike a `PowerSupply`, a temperature controller reads cryogenic
    sensors (Si diodes, RTDs, thermocouples) on multiple inputs and
    drives one or more closed-loop PID heater outputs against a
    setpoint -- there is no single voltage/current source concept.
    """

    @abstractmethod
    def get_temperature(self, input_channel: str) -> MeasurementResult:
        """Returns the temperature reading (Kelvin) for the given sensor input."""
        pass

    @abstractmethod
    def set_setpoint(self, loop: int, temperature: float) -> None:
        """Sets the control-loop setpoint temperature (Kelvin) for the given loop."""
        pass

    @abstractmethod
    def get_setpoint(self, loop: int) -> float:
        """Returns the control-loop setpoint temperature (Kelvin)."""
        pass

    @abstractmethod
    def set_pid(self, loop: int, p: float, i: float, d: float) -> None:
        """Sets the PID gains for the given control loop."""
        pass

    @abstractmethod
    def get_pid(self, loop: int) -> tuple:
        """Returns the (P, I, D) gains for the given control loop."""
        pass

    @abstractmethod
    def set_heater_range(self, loop: int, range_setting: str) -> None:
        """Sets the heater output range, e.g. 'OFF', 'LOW', 'MEDIUM', 'HIGH'."""
        pass

    @abstractmethod
    def get_heater_output(self, loop: int) -> MeasurementResult:
        """Returns the heater output level as a percentage of the current range."""
        pass

    @_unsupported
    def set_ramp_rate(self, loop: int, rate_k_per_min: float, state: bool = True) -> None:
        """Sets/enables the setpoint ramp rate in K/min (warm-up/cool-down limiting)."""

    @_unsupported
    def set_sensor_type(self, input_channel: str, sensor_type: str) -> None:
        """Configures a sensor input's type (diode, RTD, thermocouple, ...)."""

    @_unsupported
    def set_control_mode(self, loop: int, mode: str) -> None:
        """Sets the loop control mode, e.g. 'MANUAL', 'PID', 'ZONE', 'OPENLOOP'."""

    @_unsupported
    def autotune(self, loop: int, mode: str = "PI") -> None:
        """Starts the autotune routine for the given control loop."""
