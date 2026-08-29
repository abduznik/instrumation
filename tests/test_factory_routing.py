import os
import unittest
from unittest.mock import MagicMock, patch

import pyvisa

from instrumation.factory import get_instrument
from instrumation.drivers.generic import GenericDriver
from instrumation.drivers.simulated import SimulatedGeneric


def _mock_rm(idn: str):
    """Build a mock ResourceManager whose open_resource().query() returns idn."""
    rm = MagicMock()
    inst = MagicMock()
    inst.query.return_value = idn
    inst.timeout = 0
    rm.open_resource.return_value = inst
    return rm


class TestFactoryGenericFallback(unittest.TestCase):
    """Covers GH #142/#143: unrecognized IDN must never receive a
    brand-specific driver, and must resolve to the real GenericDriver."""

    def setUp(self):
        os.environ["INSTRUMATION_MODE"] = "REAL"

    def tearDown(self):
        os.environ["INSTRUMATION_MODE"] = "SIM"

    def test_unrecognized_idn_returns_generic_driver(self):
        rm = _mock_rm("ACME,WIDGET-9000,SN123,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.5::INSTR", "DMM")
        self.assertIsInstance(drv, GenericDriver)

    def test_unrecognized_idn_does_not_pick_brand_driver_when_ambiguous(self):
        # Multiple brand-specific drivers are registered under "DMM"
        # (Keithley2000, Keithley2400, ...); an unrecognized IDN must not
        # silently receive any of them.
        rm = _mock_rm("UNKNOWNCO,MODEL-1,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.6::INSTR", "DMM")
        self.assertNotIn("Keithley", drv.__class__.__name__)
        self.assertIsInstance(drv, GenericDriver)

    def test_known_brand_idn_still_routes_correctly(self):
        rm = _mock_rm("KEITHLEY INSTRUMENTS,MODEL 2000,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.7::INSTR", "DMM")
        self.assertEqual(drv.__class__.__name__, "Keithley2000")


class TestFactoryGenericSimMode(unittest.TestCase):
    """Covers GH #142/#147: SIM-mode GENERIC must not secretly be a DMM."""

    def setUp(self):
        os.environ["INSTRUMATION_MODE"] = "SIM"

    def test_sim_generic_is_not_multimeter(self):
        drv = get_instrument("USB::0x1234::SIM", "GENERIC")
        self.assertIsInstance(drv, SimulatedGeneric)
        self.assertNotEqual(drv.__class__.__name__, "SimulatedMultimeter")

    def test_sim_generic_registered_in_registry(self):
        from instrumation.drivers.registry import DriverRegistry
        drivers = DriverRegistry.get_drivers_by_type("GENERIC")
        self.assertTrue(any(d.__name__ == "SimulatedGeneric" for d in drivers))


class TestFactoryASRLSmartProbe(unittest.TestCase):
    """Covers GH #145/#150: TDK-Lambda smart probe on ASRL ports."""

    def setUp(self):
        os.environ["INSTRUMATION_MODE"] = "REAL"

    def tearDown(self):
        os.environ["INSTRUMATION_MODE"] = "SIM"

    def test_asrl_unrelated_serial_device_does_not_get_tdk_driver(self):
        # A non-TDK serial device that doesn't understand INST:NSEL should
        # fail the smart probe gracefully and fall through to IDN discovery,
        # never silently becoming a TDKLambdaZPlus.
        rm = MagicMock()
        inst = MagicMock()

        def write_side_effect(cmd):
            if cmd == "INST:NSEL 6":
                raise Exception("unsupported command")

        inst.write.side_effect = write_side_effect
        inst.query.return_value = "UNRELATED,SERIAL-DEVICE,SN1,1.0"
        rm.open_resource.return_value = inst
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("ASRL5::INSTR", "PSU")
        self.assertNotEqual(drv.__class__.__name__, "TDKLambdaZPlus")

    def test_asrl_smart_probe_disabled_for_auto_discovery(self):
        # #150: the TDK-specific INST:NSEL handshake must never be sent to
        # arbitrary serial devices during AUTO discovery. probe_asrl=False
        # is how the AUTO probe_resource path calls get_instrument.
        rm = MagicMock()
        inst = MagicMock()
        inst.query.return_value = "UNRELATED,SERIAL-DEVICE,SN1,1.0"
        rm.open_resource.return_value = inst
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("ASRL5::INSTR", "PSU", probe_asrl=False)
        writes = [c.args[0] for c in inst.write.call_args_list]
        self.assertNotIn("INST:NSEL 6", writes)


class TestFactoryIDNErrorHandling(unittest.TestCase):
    """Covers GH #149: broad except during IDN probing hides real errors."""

    def setUp(self):
        os.environ["INSTRUMATION_MODE"] = "REAL"

    def tearDown(self):
        os.environ["INSTRUMATION_MODE"] = "SIM"

    def test_identification_programming_error_propagates(self):
        # A genuine (non-transport) error during identification must surface
        # instead of being swallowed into a silent GENERIC fallback.
        rm = MagicMock()
        with patch("instrumation.factory.get_rm", return_value=rm):
            with patch(
                "instrumation.drivers.real.RealDriver.get_id",
                side_effect=AttributeError("boom"),
            ):
                with self.assertRaises(AttributeError):
                    get_instrument("TCPIP::10.0.0.8::INSTR", "DMM")

    def test_identification_visa_error_is_swallowed(self):
        # Expected transport failures (unreachable/timeout) degrade to
        # unidentified and fall back to GENERIC, not a crash.
        rm = MagicMock()
        with patch("instrumation.factory.get_rm", return_value=rm):
            with patch(
                "instrumation.drivers.real.RealDriver.get_id",
                side_effect=pyvisa.VisaIOError(1073676294),  # VI_ERROR_TMO
            ):
                drv = get_instrument("TCPIP::10.0.0.9::INSTR", "DMM")
        self.assertIsInstance(drv, GenericDriver)


if __name__ == "__main__":
    unittest.main()
