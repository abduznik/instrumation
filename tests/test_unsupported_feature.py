"""Regression tests for issue #152: _unsupported_feature must log, not print.

The method previously used ``print()``, which bypassed logging configuration
entirely -- warnings were invisible to applications capturing log records and
could not be filtered or formatted like every other library diagnostic.
"""
import logging

import pytest

from instrumation.drivers.base import InstrumentDriver
from instrumation.results import MeasurementResult


class _UnsupportedFeatureProbe(InstrumentDriver):
    """Minimal concrete driver that inherits the base-class defaults."""

    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    def write(self, command: str) -> None: ...
    def query(self, command: str) -> str:
        return ""

    def get_id(self) -> str:
        return "PROBE"

    def preset(self, automation_optimized: bool = True) -> None: ...
    def clear_status(self) -> None: ...
    def sync_config(self) -> None: ...
    def wait_ready(self, timeout: float = 30.0) -> None: ...
    def shutdown_safety(self) -> None: ...
    def check_errors(self) -> None: ...

    def measure_frequency(self) -> MeasurementResult:
        return MeasurementResult(0.0, "Hz")

    def measure_duty_cycle(self) -> MeasurementResult:
        return MeasurementResult(0.0, "%")

    def measure_v_peak_to_peak(self) -> MeasurementResult:
        return MeasurementResult(0.0, "V")


@pytest.fixture
def probe() -> InstrumentDriver:
    return _UnsupportedFeatureProbe("GPIB::1::INSTR")


def test_unsupported_feature_emits_logging_record(probe, caplog):
    """save_state() on the base class must produce a WARNING log record."""
    with caplog.at_level(logging.WARNING, logger="instrumation.drivers.base"):
        probe.save_state(3)

    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelno == logging.WARNING
    assert record.name == "instrumation.drivers.base"
    assert "'save_state'" in record.getMessage()


def test_unsupported_feature_does_not_write_to_stdout(probe, capsys):
    """No warning text may leak to stdout anymore (#152)."""
    with capsys.disabled():
        pass
    probe.save_state(3)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "not supported" not in captured.err


def test_unsupported_feature_falls_back_to_generic_name(probe, caplog):
    """An empty model string falls back to 'Instrument' (old code printed '')."""
    probe.identity["model"] = ""
    with caplog.at_level(logging.WARNING, logger="instrumation.drivers.base"):
        probe.load_state(1)

    assert len(caplog.records) == 1
    assert "is not supported by Instrument" in caplog.records[0].getMessage()


def test_unsupported_feature_includes_real_model_name(probe, caplog):
    """A populated identity dict surfaces the actual model name."""
    probe.identity["model"] = "MS2720T"
    with caplog.at_level(logging.WARNING, logger="instrumation.drivers.base"):
        probe.save_state(2)

    assert len(caplog.records) == 1
    assert "is not supported by MS2720T" in caplog.records[0].getMessage()
