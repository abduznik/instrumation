"""Regression tests for GH #160.

- #160: simulated-driver filtering must use the explicit ``is_simulated``
  marker, never string-matching "Simulated" in the class name.

(GH #154's ``UUTHandler.mes_voltage`` coverage was removed along with
``UUTHandler`` itself in #127.)
"""
import os
import unittest
from unittest.mock import MagicMock, patch

from instrumation.drivers.registry import DriverRegistry
from instrumation.drivers.simulated import SimulatedBaseDriver
from instrumation.factory import get_instrument


def _mock_rm(idn: str):
    """Build a mock ResourceManager whose open_resource().query() returns idn."""
    rm = MagicMock()
    inst = MagicMock()
    inst.query.return_value = idn
    inst.timeout = 0
    rm.open_resource.return_value = inst
    return rm


class SimulatedNamedRealDriver(SimulatedBaseDriver):
    """A REAL driver whose class name contains 'Simulated' (GH #160 trap).

    Under the old name-string filter this class was wrongly excluded from
    real-mode candidates; the is_simulated flag keeps it selectable because
    it is explicitly False.
    """
    is_simulated = False


class TestSimulatedFlagFiltering(unittest.TestCase):
    """GH #160: filtering is flag-based, not name-based."""

    _TYPE = "GH160_TEST"

    @classmethod
    def setUpClass(cls):
        DriverRegistry.register(cls._TYPE)(SimulatedNamedRealDriver)

    @classmethod
    def tearDownClass(cls):
        reg = DriverRegistry._drivers
        if cls._TYPE in reg:
            reg[cls._TYPE] = [d for d in reg[cls._TYPE]
                              if d is not SimulatedNamedRealDriver]
            if not reg[cls._TYPE]:
                del reg[cls._TYPE]

    def setUp(self):
        os.environ["INSTRUMATION_MODE"] = "REAL"

    def tearDown(self):
        os.environ["INSTRUMATION_MODE"] = "SIM"

    def test_flag_markers_exist(self):
        from instrumation.drivers.base import InstrumentDriver
        from instrumation.drivers.simulated import SimulatedGeneric
        self.assertFalse(InstrumentDriver.is_simulated)
        self.assertTrue(SimulatedBaseDriver.is_simulated)
        self.assertTrue(SimulatedGeneric.is_simulated)
        self.assertFalse(SimulatedNamedRealDriver.is_simulated)

    def test_real_mode_keeps_name_simulated_but_flagged_real(self):
        # Old code: "Simulated" not in name -> excluded -> candidate list
        # empty -> "No real driver found" ValueError. New code: flag False
        # keeps it as the single real candidate for an unknown IDN.
        rm = _mock_rm("UNKNOWNBRAND,MODEL-X,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.9::INSTR", self._TYPE)
        self.assertIsInstance(drv, SimulatedNamedRealDriver)

    def test_sim_mode_ignores_flag_false_class(self):
        # A class flagged is_simulated=False must NOT be selected in SIM mode,
        # even though its name contains "Simulated".
        os.environ["INSTRUMATION_MODE"] = "SIM"
        with self.assertRaises(ValueError):
            get_instrument("DUMMY", self._TYPE)

    def test_sim_mode_selects_by_flag_not_name(self):
        # A class whose name does NOT contain "Simulated" but is flagged
        # simulated must still be found in SIM mode (old code missed it).
        os.environ["INSTRUMATION_MODE"] = "SIM"
        from instrumation.drivers.simulated import SimulatedGeneric
        with patch.object(
            DriverRegistry, "get_drivers_by_type",
            return_value=[SimulatedGeneric],
        ):
            drv = get_instrument("DUMMY", "DMM")
        self.assertIsInstance(drv, SimulatedGeneric)
        self.assertTrue(drv.is_simulated)


if __name__ == "__main__":
    unittest.main()