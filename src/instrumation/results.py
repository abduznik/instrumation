from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Dict, List, Union
import json

try:
    import numpy as np
except ImportError:
    np = None

@dataclass
class MeasurementResult:
    """Standardized object for measurement results.

    Attributes:
        value: The measured value (float, complex, list, or numpy array).
        unit: The physical unit of the measurement (e.g., 'V', 'Hz', 'dBm').
        timestamp: The time the measurement was taken.
        status: Status of the measurement ('OK', 'ERROR', 'OVERLOAD', etc.).
        channel: Optional channel index for multi-channel instruments.
        metadata: Optional additional information from the driver.
    """
    value: Any
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "OK"
    channel: Optional[Union[int, str]] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)

    def __str__(self):
        chan_str = f" [CH {self.channel}]" if self.channel is not None else ""
        return f"{self.value} {self.unit}{chan_str} ({self.status}) @ {self.timestamp.isoformat()}"

    def to_dict(self) -> Dict[str, Any]:
        """Converts the result to a JSON-serializable dictionary."""
        val = self.value
        
        # Handle numpy arrays
        if np and isinstance(val, np.ndarray):
            val = val.tolist()
            
        # Handle complex numbers (common in VNA/IQ data)
        if isinstance(val, complex):
            val = {"real": val.real, "imag": val.imag}
        elif isinstance(val, list):
            # Recursively handle complex numbers in lists
            val = [
                {"real": v.real, "imag": v.imag} if isinstance(v, complex) else v 
                for v in val
            ]

        return {
            "value": val,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "channel": self.channel,
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """Returns the JSON string representation of the result."""
        return json.dumps(self.to_dict())
