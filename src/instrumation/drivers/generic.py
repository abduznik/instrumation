import logging
from .real import RealDriver
from .registry import register_driver

logger = logging.getLogger(__name__)

@register_driver("GENERIC")
class GenericDriver(RealDriver):
    """Fallback driver for instruments that don't match a known brand.

    Speaks plain SCPI (``*IDN?``, ``*RST``, ``*CLS``, ``SYST:ERR?``, etc.)
    via :class:`RealDriver` without sending any vendor-specific commands, so
    it's safe to use against an instrument of unknown make. It provides no
    typed measurement/config methods beyond the base contract -- callers use
    :meth:`write`/:meth:`query` directly for anything instrument-specific.
    """

    def preset(self, automation_optimized: bool = True) -> None:
        # Unknown instrument: don't assume *OPC? support, just clear and wait.
        self.write("*RST")
        self.sync_config()

    def connect(self) -> None:
        super().connect()
        logger.warning(
            f"Connected to {self.resource} using GenericDriver -- "
            f"instrument identity ({self.identity.get('manufacturer', '?')} "
            f"{self.identity.get('model', '?')}) did not match a known brand, "
            f"so only generic SCPI is available."
        )
