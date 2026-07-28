import serial
import time
from typing import List, Optional

class VisaDriver:
    """Generic wrapper for VISA instruments."""
    def __init__(self, address, timeout=5000):
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

    def query_value(self, command):
        if self.inst:
            try:
                return self.inst.query(command).strip()
            except Exception as e:
                print(f"VISA Query Error: {e}")
                return 0.0
        return 0.0

    def write(self, command):
        if self.inst:
            self.inst.write(command)

    def close(self):
        if self.inst:
            self.inst.close()
        # Note: We do NOT close the RM here as it is a global singleton

class SerialDriver:
    """Generic wrapper for Serial devices."""
    def __init__(self, port, baudrate=9600, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        try:
            self.ser = serial.Serial(port, baudrate, timeout=timeout)
            time.sleep(2) # Stabilization time
        except Exception as e:
            print(f"Error opening serial port {port}: {e}")
            self.ser = None

    def send_command(self, command_str):
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

    def read_response(self):
        if self.ser:
            try:
                return self.ser.readline().decode('utf-8').strip()
            except Exception:
                return ""
        return ""

    def close(self):
        if self.ser:
            self.ser.close()


# ── Transport utilities ────────────────────────────────────

def detect_line_termination(instrument: VisaDriver, query: str = "*IDN?") -> str:
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
    instrument: VisaDriver,
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
    instrument: VisaDriver,
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


def poll_opc_with_backoff(
    instrument: VisaDriver,
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