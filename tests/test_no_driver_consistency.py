"""Issue #146: SIM and real-hardware modes must handle an unregistered
driver_type the same way — both fail loudly.

Previously SIM raised ValueError while real mode silently fell back to
GENERIC. The fix makes real mode raise when ZERO drivers are registered
for the requested type (while keeping the #143 GENERIC fallback for the
multi-candidate / unknown-IDN case).
"""
import unittest
from unittest.mock import MagicMock, patch

from instrumation import factory
from instrumation.factory import get_instrument


class TestNoDriverFoundConsistency(unittest.TestCase):
    def tearDown(self):
        import os
        os.environ.pop("INSTRUMATION_MODE", None)

    def test_sim_mode_raises_for_unregistered_type(self):
        """SIM mode still raises for a type with no simulated driver."""
        import os
        os.environ["INSTRUMATION_MODE"] = "SIM"
        with self.assertRaises(ValueError) as cm:
            get_instrument("USB::0x1234::SIM", "INVALID_TYPE")
        self.assertIn("No simulated driver found", str(cm.exception))

    @patch.object(factory, "get_rm")
    def test_real_mode_raises_for_unregistered_type(self, mock_rm):
        """Real mode with zero registered drivers for the type must also
        raise loudly instead of silently returning a GENERIC fallback."""
        import os
        os.environ["INSTRUMATION_MODE"] = "REAL"

        rm = MagicMock()
        mock_rm.return_value = rm

        with patch.object(factory, "RealDriver") as mock_rd:
            # Unknown IDN -> no brand match -> falls through to candidate logic
            inst = MagicMock()
            inst.query.return_value = "UNKNOWN-BRAND-INSTRUMENT"
            mock_rd.return_value.inst = inst
            mock_rd.return_value.get_id.return_value = "UNKNOWN-BRAND-INSTRUMENT"
            with self.assertRaises(ValueError) as cm:
                get_instrument("TCPIP::192.168.1.9::INSTR", "INVALID_TYPE")
            self.assertIn("No real driver found", str(cm.exception))


if __name__ == "__main__":
    unittest.main()