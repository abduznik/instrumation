import json
import time
from typing import List, Dict, Any, Optional
from .base import InstrumentDriver
from ..results import MeasurementResult

class SCPIPair:
    """Represents a single SCPI command/response transaction."""
    def __init__(self, command: str, response: str, timestamp: float = None):
        self.command = command
        self.response = response
        self.timestamp = timestamp or time.time()

    def to_dict(self):
        return {
            "cmd": self.command,
            "res": self.response,
            "ts": self.timestamp
        }

class GoldenMaster:
    """Handles saving and loading of SCPI transaction logs."""
    def __init__(self, filename: str):
        self.filename = filename
        self.transactions: List[SCPIPair] = []

    def add(self, command: str, response: str):
        self.transactions.append(SCPIPair(command, response))

    def save(self):
        with open(self.filename, 'w') as f:
            json.dump([t.to_dict() for t in self.transactions], f, indent=2)

    def load(self):
        with open(self.filename, 'r') as f:
            data = json.load(f)
            self.transactions = [SCPIPair(d['cmd'], d['res'], d['ts']) for d in data]

class RecordingWrapper:
    """Wraps an existing driver to record its SCPI traffic."""
    def __init__(self, driver: InstrumentDriver, master: GoldenMaster):
        self.driver = driver
        self.master = master
        
        # Monkey patch the driver's low-level methods
        self._original_write = driver.write
        self._original_query = driver.query
        
        driver.write = self.write
        driver.query = self.query

    def write(self, command: str):
        self._original_write(command)
        self.master.add(command, "")

    def query(self, command: str) -> str:
        response = self._original_query(command)
        self.master.add(command, response)
        return response

class ReplayDriver(InstrumentDriver):
    """An instrument driver that replays responses from a Golden Master file."""
    def __init__(self, resource_address: str, master_file: str):
        super().__init__(resource_address)
        self.master = GoldenMaster(master_file)
        self.master.load()
        self.ptr = 0

    def connect(self):
        print(f"[REPLAY] Loading master from {self.master.filename}")

    def disconnect(self):
        print("[REPLAY] Finished replay session")

    def write(self, command: str):
        # In replay mode, we just advance the pointer if the command matches
        if self.ptr < len(self.master.transactions):
            expected = self.master.transactions[self.ptr].command
            if command.strip().upper() == expected.strip().upper():
                print(f"[REPLAY] Write: {command} (Matched)")
                self.ptr += 1
            else:
                print(f"[REPLAY] Warning: command mismatch. Expected '{expected}', got '{command}'")
        else:
             print(f"[REPLAY] Warning: end of log reached. Ignoring write '{command}'")

    def query(self, command: str) -> str:
        if self.ptr < len(self.master.transactions):
            tx = self.master.transactions[self.ptr]
            if command.strip().upper() == tx.command.strip().upper():
                print(f"[REPLAY] Query: {command} -> {tx.response}")
                self.ptr += 1
                return tx.response
            else:
                print(f"[REPLAY] Warning: command mismatch. Expected '{tx.command}', got '{command}'")
                return "0"
        return "0"

    # Minimal implementations for abstract methods
    # These will use query/write which are replayed
    def get_id(self): return self.query("*IDN?")
    def measure_voltage(self): return MeasurementResult(float(self.query("MEAS:VOLT?")), "V")
    def measure_resistance(self): return MeasurementResult(float(self.query("MEAS:RES?")), "Ohm")
    def measure_frequency(self): return MeasurementResult(float(self.query("MEAS:FREQ?")), "Hz")
    def measure_duty_cycle(self): return MeasurementResult(float(self.query("MEAS:DUTY?")), "%")
    def measure_v_peak_to_peak(self): return MeasurementResult(float(self.query("MEAS:PKPK?")), "Vpp")
