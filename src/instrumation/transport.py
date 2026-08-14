"""Low-level transport wrappers and SCPI handshake helpers.

Provides thin connection wrappers for the two physical transports the library
speaks -- VISA (:class:`VisaDriver`) and raw serial (:class:`SerialDriver`) --
plus helpers for the handshake problems that come up when talking to real
instruments: guessing line terminations, finding a workable timeout, and
waiting for an operation to finish without blind sleeps.

Both wrapper classes are deliberately forgiving: a failed connection leaves the
object usable but inert rather than raising. See the individual docstrings for
what that means for callers.
"""

import asyncio
import serial # type: ignore
import time
from typing import List, Optional, Tuple, Union, Any

class VisaDriver:
    """Generic wrapper for VISA instruments.

    Opens a VISA resource on construction and clears its status register.

    Parameters
    ----------
    address : str
        VISA resource string, for example ``"TCPIP::192.168.1.5::INSTR"``.
    timeout : int, optional
        Read timeout in milliseconds, applied to the opened resource.
        Defaults to ``5000``.

    Notes
    -----
    Construction never raises. If the resource cannot be opened, the error is
    printed and :attr:`inst` is set to ``None``, leaving an object whose methods
    are all no-ops. Check ``driver.inst is not None`` before relying on it.

    Attributes
    ----------
    rm : pyvisa.ResourceManager
        The shared resource manager from :func:`~instrumation.factory.get_rm`.
    address : str
        The resource address this driver was constructed with.
    inst : pyvisa.Resource or None
        The open resource, or ``None`` if the connection failed.
    """
    def __init__(self, address: str, timeout: int = 5000) -> None:
        from .factory import get_rm
        self.rm = get_rm()
        self.address = address
        try:
            self.inst = self.rm.open_resource(address)
            self.inst.timeout = timeout
            self.inst.write("*CLS")
        except Exception as e:
            print(f"Error connecting to {address}: {e}")
            self.inst = None

    def query_value(self, command: str) -> Union[str, float]:
        """Send a query and return the stripped response.

        Parameters
        ----------
        command : str
            SCPI query to send, for example ``"MEAS:VOLT:DC?"``.

        Returns
        -------
        str or float
            The stripped response string on success. Returns the float ``0.0``
            if the query raised, or if the driver never connected.

        Notes
        -----
        The ``0.0`` fallback is indistinguishable from a genuine ``0.0``
        reading, and the two failure modes return a different *type* to the
        success path. Callers that need to tell a real zero from a failed read
        should check ``self.inst`` first and use the underlying resource
        directly.
        """
        if self.inst:
            try:
                return self.inst.query(command).strip()
            except Exception as e:
                print(f"VISA Query Error: {e}")
                return 0.0
        return 0.0

    def write(self, command: str) -> None:
        """Send a command without reading a response.

        Parameters
        ----------
        command : str
            SCPI command to send, for example ``"OUTP ON"``.

        Notes
        -----
        Silently does nothing if the driver never connected. Unlike
        :meth:`query_value`, write errors are *not* caught and will propagate.
        """
        if self.inst:
            self.inst.write(command)

    def close(self) -> None:
        """Close the VISA resource, leaving the shared resource manager open.

        Safe to call when the driver never connected. The resource manager is
        a process-wide singleton shared with every other driver, so it is
        deliberately not closed here.
        """
        if self.inst:
            self.inst.close()
        # Note: We do NOT close the RM here as it is a global singleton

class SerialDriver:
    """Generic wrapper for Serial devices.

    Opens the port on construction and waits two seconds for the device to
    stabilise, which many USB-serial adapters need before they will accept
    traffic.

    Parameters
    ----------
    port : str
        Device path or COM port name, for example ``"COM3"`` or
        ``"/dev/ttyUSB0"``.
    baudrate : int, optional
        Baud rate. Defaults to ``9600``.
    timeout : float, optional
        Read timeout in seconds. Defaults to ``1``.

    Notes
    -----
    Construction never raises. If the port cannot be opened the error is
    printed and :attr:`ser` is set to ``None``, leaving an object whose methods
    are all no-ops. Check ``driver.ser is not None`` before relying on it.

    Because of the stabilisation wait, constructing this class blocks for
    roughly two seconds even when the port opens immediately.

    Attributes
    ----------
    port : str
        Device path or COM port name.
    baudrate : int
        Configured baud rate.
    timeout : float
        Read timeout in seconds.
    ser : serial.Serial or None
        The open port, or ``None`` if it could not be opened.
    """
    def __init__(self, port, baudrate: int = 9600, timeout: float = 1) -> None :
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        try:
            self.ser = serial.Serial(port, baudrate, timeout=timeout)
            time.sleep(2) # Stabilization time
        except Exception as e:
            print(f"Error opening serial port {port}: {e}")
            self.ser = None

    def send_command(self, command_str: Union[str, bytes]) -> None:
        """Write a command to the port, appending a newline if needed.

        Parameters
        ----------
        command_str : str or bytes
            The command to send. A ``str`` is encoded as UTF-8 and gets a
            trailing ``\\n`` appended unless it already ends with one. ``bytes``
            are written through unchanged, with no terminator added.

        Notes
        -----
        Silently does nothing if the port never opened, and write errors are
        caught and printed rather than raised -- so a successful return does
        not guarantee the command reached the device.
        """
        if self.ser:
            try:
                # Handle both bytes and string input
                if isinstance(command_str, str):
                    data = command_str.encode('utf-8')
                    if not command_str.endswith('\n'):
                         data += b'\n'
                else:
                    data = command_str
                
                self.ser.write(data)
            except Exception as e:
                print(f"Serial Write Error: {e}")

    def read_response(self) -> str:
        """Read one newline-terminated line and return it stripped.

        Returns
        -------
        str
            The decoded, stripped line. Returns ``""`` on a read error, if the
            port never opened, or if the read timed out with no data.

        Notes
        -----
        An empty string is ambiguous -- it covers a timeout, a decode failure,
        and a device that genuinely sent a blank line. Blocks up to
        :attr:`timeout` seconds.
        """
        if self.ser:
            try:
                return self.ser.readline().decode('utf-8').strip()
            except Exception:
                return ""
        return ""

    def close(self) -> None:
        """Close the serial port. Safe to call if it never opened."""
        if self.ser:
            self.ser.close()


# ── Transport utilities ────────────────────────────────────

def detect_line_termination(instrument: Any, query: str = "*IDN?") -> str:
    """Detect which line-termination character an instrument responds to.

    Tries each common terminator (LF, CR, CRLF) against a safe SCPI query
    and returns the first one that produces a valid response.

    Steps:
        1. Save the instrument's current read_termination setting.
        2. For each candidate terminator in ["\\n", "\\r", "\\r\\n"]:
           a. Set instrument.read_termination to the candidate.
           b. Send the query (default "*IDN?").
           c. If the response is non-empty and looks like a valid *IDN? reply
              (contains at least one comma), return the candidate terminator.
        3. If none work, restore the original termination and raise RuntimeError.
        4. Restore the original termination before returning.

    Args:
        instrument: A connected VisaDriver or pyvisa Resource object with
            .write(), .query(), and .read_termination attributes.
        query: The SCPI query to test with. Defaults to "*IDN?".

    Returns:
        The working terminator string: "\\n", "\\r", or "\\r\\n".

    Raises:
        RuntimeError: If no candidate terminator produces a valid response.
    """
    original_termination = instrument.read_termination

    for candidate in ["\n", "\r", "\r\n"]:
        instrument.read_termination = candidate
        try:
            response = instrument.query(query)
            if response and "," in response:
                instrument.read_termination = original_termination
                return candidate
        except Exception:
            continue

    instrument.read_termination = original_termination
    raise RuntimeError(f"No terminator produced a valid response for query: {query}")


def find_minimum_timeout(
    instrument: Any,
    query: str = "*IDN?",
    candidates: Optional[List[int]] = None,
) -> int:
    """Find the smallest safe timeout value for an instrument.

    Tries a list of candidate timeout values (in milliseconds) against a safe
    SCPI query and returns the first one that completes without timing out.

    Steps:
        1. If candidates is None, use [100, 250, 500, 1000, 2500, 5000].
        2. Save the instrument's current timeout setting.
        3. Sort candidates ascending (smallest first).
        4. For each candidate timeout:
           a. Set instrument.timeout to the candidate.
           b. Send the query.
           c. If the response is non-empty, restore the original timeout and
              return the candidate.
           d. If a VisaIOError or timeout exception occurs, continue to the next.
        5. If no candidate works, restore the original timeout and raise RuntimeError.

    Args:
        instrument: A connected VisaDriver or pyvisa Resource object with
            .write(), .query(), and .timeout attributes.
        query: The SCPI query to test with. Defaults to "*IDN?".
        candidates: List of timeout values in ms to try. Defaults to
            [100, 250, 500, 1000, 2500, 5000].

    Returns:
        The smallest timeout value (in ms) that worked.

    Raises:
        RuntimeError: If no candidate timeout produces a valid response.
    """
    if candidates is None:
        candidates = [100, 250, 500, 1000, 2500, 5000]

    original_timeout = instrument.timeout
    candidates_sorted = sorted(candidates)

    for candidate in candidates_sorted:
        instrument.timeout = candidate
        try:
            response = instrument.query(query)
            if response:
                instrument.timeout = original_timeout
                return candidate
        except (TimeoutError, Exception):
            continue

    instrument.timeout = original_timeout
    raise RuntimeError(f"No timeout candidate worked for query: {query}")


def poll_for_mav(
    instrument: Any,
    timeout: float = 10.0,
    poll_interval: float = 0.1,
) -> None:
    """Poll an instrument's status byte for the MAV (Message Available) bit.

    Instead of reading immediately or sleeping blindly, this polls the Status
    Byte Register (STB) until bit 4 (MAV) is set, indicating the instrument
    has data ready to read.

    Steps:
        1. Record the start time.
        2. Loop until timeout is exceeded:
           a. Send "*STB?" or "STB?" to read the status byte.
           b. Parse the response as an integer.
           c. If bit 4 (value & 0x10) is set, return — data is ready.
           d. Sleep for poll_interval seconds.
        3. If the loop exits without MAV being set, raise InstrumentTimeout.

    Args:
        instrument: A connected VisaDriver or pyvisa Resource object.
        timeout: Maximum seconds to wait for MAV. Defaults to 10.0.
        poll_interval: Seconds between polls. Defaults to 0.1.

    Raises:
        InstrumentTimeout: If MAV is not set within the timeout period.
    """
    from .exceptions import InstrumentTimeout

    start = time.time()
    while time.time() - start < timeout:
        try:
            response = instrument.query("*STB?")
            value = int(response)
            if value & 0x10:
                return
        except (ValueError, Exception):
            pass
        time.sleep(poll_interval)

    raise InstrumentTimeout(f"MAV bit not set within {timeout}s timeout")


async def poll_for_mav_async(
    instrument: Any,
    timeout: float = 10.0,
    poll_interval: float = 0.1,
) -> None:
    """Async variant of :func:`poll_for_mav`, using ``asyncio.sleep``.

    Identical polling behavior to the sync version, but non-blocking so it
    can run alongside other coroutines in an async context.

    Args:
        instrument: A connected VisaDriver or pyvisa Resource object.
        timeout: Maximum seconds to wait for MAV. Defaults to 10.0.
        poll_interval: Seconds between polls. Defaults to 0.1.

    Raises:
        InstrumentTimeout: If MAV is not set within the timeout period.
    """
    from .exceptions import InstrumentTimeout

    start = time.time()
    while time.time() - start < timeout:
        try:
            response = instrument.query("*STB?")
            value = int(response)
            if value & 0x10:
                return
        except (ValueError, Exception):
            pass
        await asyncio.sleep(poll_interval)

    raise InstrumentTimeout(f"MAV bit not set within {timeout}s timeout")


def poll_opc_with_backoff(
    instrument: Any,
    timeout: float = 30.0,
    initial_delay: float = 0.1,
    max_delay: float = 1.0,
) -> None:
    """Poll for operation-complete (*OPC?) with exponential backoff delay.

    Sends *OPC? and waits for "1" as the response, but instead of polling at
    a fixed interval, uses exponential backoff to reduce bus traffic during
    long operations while still responding quickly to fast completions.

    Steps:
        1. Record the start time. Set current_delay = initial_delay.
        2. Loop until timeout is exceeded:
           a. Send "*OPC?" and read the response.
           b. If the response stripped is "1", return — operation complete.
           c. Sleep for current_delay seconds.
           d. Multiply current_delay by 2, capped at max_delay.
        3. If the loop exits without completion, raise InstrumentTimeout.

    Args:
        instrument: A connected VisaDriver or pyvisa Resource object.
        timeout: Maximum seconds to wait. Defaults to 30.0.
        initial_delay: Starting poll delay in seconds. Defaults to 0.1.
        max_delay: Maximum delay between polls in seconds. Defaults to 1.0.

    Raises:
        InstrumentTimeout: If *OPC? does not return "1" within the timeout.
    """
    from .exceptions import InstrumentTimeout

    start = time.time()
    current_delay = initial_delay

    while time.time() - start < timeout:
        try:
            response = instrument.query("*OPC?")
            if response.strip() == "1":
                return
        except Exception:
            pass
        time.sleep(current_delay)
        current_delay = min(current_delay * 2, max_delay)

    raise InstrumentTimeout(f"Operation did not complete within {timeout}s timeout")


def batch_query(
    instrument: Any,
    queries: List[str],
    stop_on_error: bool = False,
    write_then_read: Optional[List[Tuple[str, str]]] = None,
) -> dict:
    """Send multiple SCPI queries and return a dictionary of results.

    This is useful for fetching multiple instrument settings or readings in
    a single call, reducing round-trips and improving efficiency on slow
    connections. Failed queries are logged with their error messages rather
    than raising immediately (unless stop_on_error=True).

    Steps:
        1. Initialize an empty results dictionary.
        2. For each query in the list:
           a. Send the query via instrument.query().
           b. Store the stripped response in results[query].
           c. If the query fails and stop_on_error is True, raise the exception.
           d. If stop_on_error is False, store the error message as the value.
        3. For each (write_cmd, read_cmd) pair in write_then_read:
           a. Send write_cmd via instrument.write(), then read_cmd via instrument.query().
           b. Store the stripped response in results[write_cmd].
           c. Same stop_on_error/error-message behavior as queries.
        4. Return the results dictionary.

    Args:
        instrument: A connected VisaDriver or pyvisa Resource object.
        queries: List of SCPI query strings to send.
        stop_on_error: If True, raise on first error. If False (default),
            store error messages and continue with remaining queries.
        write_then_read: Optional list of (write_cmd, read_cmd) pairs for
            instruments that need a separate write before the read (e.g.
            writing a register address, then reading its value). Results
            are keyed by write_cmd.

    Returns:
        A dictionary mapping each query string (or write_then_read write_cmd)
        to its response (or error message).

    Example:
        >>> results = batch_query(dmm, ["*IDN?", "MEAS:VOLT:DC?", "*STB?"])
        >>> for cmd, resp in results.items():
        ...     print(f"{cmd} -> {resp}")

        >>> results = batch_query(inst, [], write_then_read=[("REG 0", "REG?")])
        >>> results["REG 0"]
    """
    results = {}
    for query in queries:
        try:
            response = instrument.query(query)
            results[query] = response.strip() if isinstance(response, str) else response
        except Exception as e:
            if stop_on_error:
                raise
            results[query] = f"ERROR: {e}"

    for write_cmd, read_cmd in write_then_read or []:
        try:
            instrument.write(write_cmd)
            response = instrument.query(read_cmd)
            results[write_cmd] = response.strip() if isinstance(response, str) else response
        except Exception as e:
            if stop_on_error:
                raise
            results[write_cmd] = f"ERROR: {e}"

    return results