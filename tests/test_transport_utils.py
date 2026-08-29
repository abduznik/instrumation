"""Tests for transport and scanner utility functions."""

import os
import pytest
from unittest.mock import MagicMock

from instrumation.transport import (
    VisaDriver,
    detect_line_termination,
    find_minimum_timeout,
    poll_for_mav,
    poll_for_mav_async,
    poll_opc_with_backoff,
    batch_query,
)
from instrumation.scanner import find_duplicate_addresses
from instrumation.exceptions import InstrumentTimeout


# ── detect_line_termination ────────────────────────────────

class TestDetectLineTermination:
    """Tests for detect_line_termination()."""

    def test_returns_valid_terminator(self):
        """The return value must be one of the three standard terminators."""
        mock_inst = MagicMock()
        mock_inst.read_termination = "\n"
        mock_inst.query.return_value = "SIM,SIM_DMM,123,1.0"

        result = detect_line_termination(mock_inst, query="*IDN?")
        assert result in ["\n", "\r", "\r\n"]

    def test_tries_all_terminators(self):
        """Should iterate through LF, CR, CRLF and return the first that works."""
        mock_inst = MagicMock()
        mock_inst.read_termination = "\n"
        mock_inst.query.return_value = "SIM,SIM_DMM,123,1.0"

        detect_line_termination(mock_inst, query="*IDN?")
        assert mock_inst.query.called
        assert mock_inst.read_termination == "\n"

    def test_raises_on_no_valid_terminator(self):
        """Should raise RuntimeError when no terminator produces a valid response."""
        mock_inst = MagicMock()
        mock_inst.read_termination = "\n"
        mock_inst.query.return_value = ""

        with pytest.raises(RuntimeError):
            detect_line_termination(mock_inst, query="*IDN?")

    def test_restores_original_termination(self):
        """Must restore read_termination to its original value after testing."""
        mock_inst = MagicMock()
        mock_inst.read_termination = "\r\n"
        mock_inst.query.return_value = "SIM,SIM_DMM,123,1.0"

        detect_line_termination(mock_inst, query="*IDN?")
        assert mock_inst.read_termination == "\r\n"


# ── find_minimum_timeout ───────────────────────────────────

class TestFindMinimumTimeout:
    """Tests for find_minimum_timeout()."""

    def test_returns_int_milliseconds(self):
        """Return value must be an int representing milliseconds."""
        mock_inst = MagicMock()
        mock_inst.timeout = 5000
        mock_inst.query.return_value = "SIM,SIM_DMM,123,1.0"

        result = find_minimum_timeout(mock_inst, query="*IDN?")
        assert isinstance(result, int)
        assert result > 0

    def test_returns_smallest_working_timeout(self):
        """Should return the smallest candidate that doesn't time out."""
        mock_inst = MagicMock()
        mock_inst.timeout = 5000
        mock_inst.query.return_value = "SIM,SIM_DMM,123,1.0"

        result = find_minimum_timeout(
            mock_inst, query="*IDN?", candidates=[100, 500, 1000, 5000]
        )
        assert result == 100

    def test_skips_timeouts_that_fail(self):
        """Should skip candidates that raise timeout errors and try the next."""
        mock_inst = MagicMock()
        mock_inst.timeout = 5000
        mock_inst.query.side_effect = [
            TimeoutError("timeout"),
            TimeoutError("timeout"),
            "SIM,SIM_DMM,123,1.0",
        ]

        result = find_minimum_timeout(
            mock_inst, query="*IDN?", candidates=[100, 250, 500]
        )
        assert result == 500

    def test_raises_when_all_fail(self):
        """Should raise RuntimeError if no candidate timeout works."""
        mock_inst = MagicMock()
        mock_inst.timeout = 5000
        mock_inst.query.side_effect = TimeoutError("always times out")

        with pytest.raises(RuntimeError):
            find_minimum_timeout(mock_inst, query="*IDN?", candidates=[100, 250])

    def test_restores_original_timeout(self):
        """Must restore the instrument's timeout to its original value."""
        mock_inst = MagicMock()
        mock_inst.timeout = 5000
        mock_inst.query.return_value = "SIM,SIM_DMM,123,1.0"

        find_minimum_timeout(mock_inst, query="*IDN?")
        assert mock_inst.timeout == 5000


# ── poll_for_mav ───────────────────────────────────────────

class TestPollForMav:
    """Tests for poll_for_mav()."""

    def test_returns_when_mav_set(self):
        """Should return (not raise) once MAV bit (0x10) is detected."""
        mock_inst = MagicMock()
        mock_inst.query.return_value = "16"

        poll_for_mav(mock_inst, timeout=1.0, poll_interval=0.01)

    def test_raises_on_timeout(self):
        """Should raise InstrumentTimeout if MAV never appears."""
        mock_inst = MagicMock()
        mock_inst.query.return_value = "0"

        with pytest.raises(InstrumentTimeout):
            poll_for_mav(mock_inst, timeout=0.2, poll_interval=0.05)

    def test_polls_multiple_times(self):
        """Should call query multiple times before MAV is set."""
        mock_inst = MagicMock()
        mock_inst.query.side_effect = ["0", "0", "0", "16"]

        poll_for_mav(mock_inst, timeout=2.0, poll_interval=0.01)
        assert mock_inst.query.call_count == 4


# ── poll_for_mav_async ──────────────────────────────────────

class TestPollForMavAsync:
    """Tests for poll_for_mav_async()."""

    @pytest.mark.asyncio
    async def test_returns_when_mav_set(self):
        """Should return (not raise) once MAV bit (0x10) is detected."""
        mock_inst = MagicMock()
        mock_inst.query.return_value = "16"

        await poll_for_mav_async(mock_inst, timeout=1.0, poll_interval=0.01)

    @pytest.mark.asyncio
    async def test_raises_on_timeout(self):
        """Should raise InstrumentTimeout if MAV never appears."""
        mock_inst = MagicMock()
        mock_inst.query.return_value = "0"

        with pytest.raises(InstrumentTimeout):
            await poll_for_mav_async(mock_inst, timeout=0.2, poll_interval=0.05)

    @pytest.mark.asyncio
    async def test_polls_multiple_times(self):
        """Should call query multiple times before MAV is set."""
        mock_inst = MagicMock()
        mock_inst.query.side_effect = ["0", "0", "0", "16"]

        await poll_for_mav_async(mock_inst, timeout=2.0, poll_interval=0.01)
        assert mock_inst.query.call_count == 4


# ── poll_opc_with_backoff ──────────────────────────────────

class TestPollOpcWithBackoff:
    """Tests for poll_opc_with_backoff()."""

    def test_returns_when_opc(self):
        """Should return once *OPC? returns '1'."""
        mock_inst = MagicMock()
        mock_inst.query.return_value = "1"

        poll_opc_with_backoff(mock_inst, timeout=5.0)

    def test_raises_on_timeout(self):
        """Should raise InstrumentTimeout if *OPC? never returns '1'."""
        mock_inst = MagicMock()
        mock_inst.query.return_value = "0"

        with pytest.raises(InstrumentTimeout):
            poll_opc_with_backoff(mock_inst, timeout=0.3, initial_delay=0.05)

    def test_uses_increasing_delays(self):
        """Delays between polls should grow (exponential backoff) up to max_delay."""
        mock_inst = MagicMock()
        mock_inst.query.side_effect = ["0", "0", "0", "1"]

        poll_opc_with_backoff(
            mock_inst, timeout=10.0, initial_delay=0.01, max_delay=0.5
        )
        assert mock_inst.query.call_count == 4


# ── find_duplicate_addresses ───────────────────────────────

class TestFindDuplicateAddresses:
    """Tests for find_duplicate_addresses()."""

    def test_returns_empty_for_no_duplicates(self):
        """No duplicate addresses → empty list."""
        devices = [
            {"type": "visa", "id": "USB::1", "desc": "DMM"},
            {"type": "visa", "id": "USB::2", "desc": "PSU"},
        ]
        result = find_duplicate_addresses(devices)
        assert result == []

    def test_finds_duplicate_with_different_identities(self):
        """Same address with different desc values should be flagged."""
        devices = [
            {"type": "visa", "id": "GPIB::1", "desc": "Keysight DMM"},
            {"type": "visa", "id": "GPIB::1", "desc": "Rohde Schwarz SG"},
        ]
        result = find_duplicate_addresses(devices)
        assert len(result) == 1
        assert result[0]["address"] == "GPIB::1"
        assert "Keysight DMM" in result[0]["identities"]
        assert "Rohde Schwarz SG" in result[0]["identities"]

    def test_ignores_same_identity_duplicates(self):
        """Same address with same desc is not a conflict (just a re-scan)."""
        devices = [
            {"type": "visa", "id": "USB::1", "desc": "DMM"},
            {"type": "visa", "id": "USB::1", "desc": "DMM"},
        ]
        result = find_duplicate_addresses(devices)
        assert result == []

    def test_returns_list_of_dicts_with_correct_keys(self):
        """Each conflict entry must have 'address', 'identities', and 'count'."""
        devices = [
            {"type": "visa", "id": "GPIB::5", "desc": "Scope A"},
            {"type": "visa", "id": "GPIB::5", "desc": "Scope B"},
            {"type": "visa", "id": "GPIB::5", "desc": "Scope C"},
        ]
        result = find_duplicate_addresses(devices)
        assert len(result) == 1
        assert set(result[0].keys()) == {"address", "identities", "count"}
        assert result[0]["count"] == 3

    def test_handles_multiple_conflicts(self):
        """Should detect multiple independent address conflicts."""
        devices = [
            {"type": "visa", "id": "GPIB::1", "desc": "DMM A"},
            {"type": "visa", "id": "GPIB::1", "desc": "DMM B"},
            {"type": "visa", "id": "GPIB::2", "desc": "PSU A"},
            {"type": "visa", "id": "GPIB::2", "desc": "PSU B"},
        ]
        result = find_duplicate_addresses(devices)
        assert len(result) == 2
        addresses = [r["address"] for r in result]
        assert "GPIB::1" in addresses
        assert "GPIB::2" in addresses


# ── batch_query ─────────────────────────────────────────────

class TestBatchQuery:
    """Tests for batch_query()."""

    def test_returns_dict_with_all_queries(self):
        """Should return a dict with one entry per query."""
        mock_inst = MagicMock()
        mock_inst.query.side_effect = ["SIM,SIM_DMM,1.0", "3.3", "0"]

        result = batch_query(mock_inst, ["*IDN?", "MEAS:VOLT:DC?", "*STB?"])
        assert len(result) == 3
        assert "*IDN?" in result
        assert "MEAS:VOLT:DC?" in result
        assert "*STB?" in result

    def test_returns_stripped_responses(self):
        """Responses should be stripped of whitespace."""
        mock_inst = MagicMock()
        mock_inst.query.return_value = "  3.3V  \n"

        result = batch_query(mock_inst, ["MEAS:VOLT:DC?"])
        assert result["MEAS:VOLT:DC?"] == "3.3V"

    def test_continues_on_error_by_default(self):
        """Should continue processing remaining queries when one fails."""
        mock_inst = MagicMock()
        mock_inst.query.side_effect = [
            "SIM,SIM_DMM,1.0",
            Exception("Timeout"),
            "0",
        ]

        result = batch_query(mock_inst, ["*IDN?", "FAIL?", "*STB?"])
        assert result["*IDN?"] == "SIM,SIM_DMM,1.0"
        assert "ERROR:" in result["FAIL?"]
        assert result["*STB?"] == "0"

    def test_stops_on_error_when_enabled(self):
        """Should raise immediately when stop_on_error=True and a query fails."""
        mock_inst = MagicMock()
        mock_inst.query.side_effect = [
            "SIM,SIM_DMM,1.0",
            Exception("Timeout"),
        ]

        with pytest.raises(Exception, match="Timeout"):
            batch_query(mock_inst, ["*IDN?", "FAIL?"], stop_on_error=True)

    def test_empty_query_list(self):
        """Should return empty dict for empty query list."""
        mock_inst = MagicMock()
        result = batch_query(mock_inst, [])
        assert result == {}

    def test_single_query(self):
        """Should work with a single query."""
        mock_inst = MagicMock()
        mock_inst.query.return_value = "1.234"

        result = batch_query(mock_inst, ["MEAS:VOLT?"])
        assert result == {"MEAS:VOLT?": "1.234"}

    def test_preserves_query_order_in_keys(self):
        """Dictionary keys should match the input query order."""
        mock_inst = MagicMock()
        mock_inst.query.side_effect = ["A", "B", "C"]

        result = batch_query(mock_inst, ["CMD_C", "CMD_A", "CMD_B"])
        assert list(result.keys()) == ["CMD_C", "CMD_A", "CMD_B"]

    def test_write_then_read_only(self):
        """Should work with only write_then_read pairs and no queries."""
        mock_inst = MagicMock()
        mock_inst.query.return_value = "42"

        result = batch_query(mock_inst, [], write_then_read=[("REG 0", "REG?")])
        assert result == {"REG 0": "42"}
        mock_inst.write.assert_called_once_with("REG 0")
        mock_inst.query.assert_called_once_with("REG?")

    def test_write_then_read_mixed_with_queries(self):
        """Should combine plain queries and write_then_read pairs in one result dict."""
        mock_inst = MagicMock()
        mock_inst.query.side_effect = ["SIM,SIM_DMM,1.0", "42"]

        result = batch_query(
            mock_inst,
            ["*IDN?"],
            write_then_read=[("REG 0", "REG?")],
        )
        assert result["*IDN?"] == "SIM,SIM_DMM,1.0"
        assert result["REG 0"] == "42"

    def test_write_then_read_error_continues_by_default(self):
        """A failing write_then_read pair should store an error and continue."""
        mock_inst = MagicMock()
        mock_inst.write.side_effect = Exception("bus error")

        result = batch_query(mock_inst, [], write_then_read=[("REG 0", "REG?")])
        assert "ERROR:" in result["REG 0"]
    def test_write_then_read_stops_on_error_when_enabled(self):
        """Should raise immediately when stop_on_error=True and write/read fails."""
        mock_inst = MagicMock()
        mock_inst.write.side_effect = Exception("bus error")

        with pytest.raises(Exception, match="bus error"):
            batch_query(
                mock_inst, [], write_then_read=[("REG 0", "REG?")], stop_on_error=True
            )


# ── VisaDriver.query_value ─────────────────────────────────

class TestVisaDriverQueryValue:
    """Tests for VisaDriver.query_value() error contract (gh #153).

    A failed read must return None, never a float 0.0 that could pass for
    a genuine zero reading. The driver is built via object.__new__ so the
    VISA backend is never touched; we only exercise query_value() itself.
    """

    @staticmethod
    def make_driver(inst):
        drv = object.__new__(VisaDriver)
        drv.rm = MagicMock()
        drv.address = "TCPIP::127.0.0.1::INSTR"
        drv.inst = inst
        return drv

    def test_success_returns_stripped_string(self):
        """A successful query returns the stripped response string."""
        inst = MagicMock()
        inst.query.return_value = " 3.300000E+00\n"
        drv = self.make_driver(inst)

        result = drv.query_value("MEAS:VOLT:DC?")
        assert result == "3.300000E+00"
        assert isinstance(result, str)
        inst.query.assert_called_once_with("MEAS:VOLT:DC?")

    def test_genuine_zero_reading_is_string(self):
        """A real 0.0 reading from the instrument survives as the string '0.0'."""
        inst = MagicMock()
        inst.query.return_value = "0.0\n"
        drv = self.make_driver(inst)

        result = drv.query_value("MEAS:VOLT:DC?")
        assert result == "0.0"

    def test_query_error_returns_none_not_zero(self):
        """A query that raises must return None, never a float 0.0."""
        inst = MagicMock()
        inst.query.side_effect = Exception("VISA timeout")
        drv = self.make_driver(inst)

        result = drv.query_value("MEAS:VOLT:DC?")
        assert result is None

    def test_never_connected_returns_none_not_zero(self):
        """A driver with no open resource must return None, never float 0.0."""
        drv = self.make_driver(None)

        result = drv.query_value("MEAS:VOLT:DC?")
        assert result is None


# ── VisaDriver.write ───────────────────────────────────────

class TestVisaDriverWrite:
    """Tests for VisaDriver.write() error contract (gh #163).

    write() must follow the same forgiving contract as query_value() and
    SerialDriver.send_command: a failed write is caught and printed, never
    raised, and a never-connected driver is a silent no-op.
    """

    @staticmethod
    def make_driver(inst):
        drv = object.__new__(VisaDriver)
        drv.rm = MagicMock()
        drv.address = "TCPIP::127.0.0.1::INSTR"
        drv.inst = inst
        return drv

    def test_success_forwards_to_resource(self):
        """A successful write must reach the underlying VISA resource."""
        inst = MagicMock()
        drv = self.make_driver(inst)

        drv.write("OUTP ON")
        inst.write.assert_called_once_with("OUTP ON")

    def test_write_error_is_caught_not_raised(self):
        """A VISA write error must be caught (printed), not propagated."""
        inst = MagicMock()
        inst.write.side_effect = Exception("VISA bus error")
        drv = self.make_driver(inst)

        drv.write("OUTP ON")  # must not raise

    def test_write_never_connected_is_noop(self):
        """A driver with no open resource must silently do nothing."""
        drv = self.make_driver(None)

        drv.write("OUTP ON")  # must not raise
