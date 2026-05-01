import pytest
from instrumation.exceptions import (
    InstrumentError,
    InstrumentTimeout,
    ConnectionLost,
    OverloadError,
    ConfigurationError
)

def test_exception_hierarchy():
    """Verify that all exceptions inherit from InstrumentError."""
    assert issubclass(InstrumentTimeout, InstrumentError)
    assert issubclass(ConnectionLost, InstrumentError)
    assert issubclass(OverloadError, InstrumentError)
    assert issubclass(ConfigurationError, InstrumentError)

def test_exception_messages():
    """Verify that exceptions can be raised with a message."""
    with pytest.raises(InstrumentTimeout) as excinfo:
        raise InstrumentTimeout("Timeout occurred")
    assert str(excinfo.value) == "Timeout occurred"

    with pytest.raises(ConnectionLost) as excinfo:
        raise ConnectionLost("Connection lost")
    assert str(excinfo.value) == "Connection lost"
