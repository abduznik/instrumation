from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

@dataclass
class MeasurementResult:
    """Standardized object for measurement results.

    Attributes:
        value: The measured value (typically float or list of floats).
        unit: The physical unit of the measurement (e.g., 'V', 'Hz', 'dBm').
        timestamp: The time the measurement was taken.
        status: Status of the measurement ('OK', 'ERROR', 'OVERLOAD', etc.).
        metadata: Optional additional information from the driver.
    """
    value: Any
    unit: str
    timestamp: datetime = datetime.now()
    status: str = "OK"
    metadata: Optional[dict] = None

    def __str__(self):
        return f"{self.value} {self.unit} ({self.status}) @ {self.timestamp.isoformat()}"
