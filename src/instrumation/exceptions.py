class InstrumentError(Exception):
    """Base class for all instrument-related errors."""
    pass

class InstrumentTimeout(InstrumentError):
    """Raised when an instrument operation times out."""
    pass

class ConnectionLost(InstrumentError):
    """Raised when the connection to an instrument is unexpectedly closed or lost."""
    pass

class OverloadError(InstrumentError):
    """Raised when an instrument detects an input overload condition."""
    pass

class ConfigurationError(InstrumentError):
    """Raised when an invalid configuration or command is sent to the instrument."""
    pass
