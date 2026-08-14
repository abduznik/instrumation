import unittest
import os

from instrumation.drivers.registry import DriverRegistry
from instrumation.drivers.generic import GenericDriver
from instrumation.drivers.simulated import SimulatedGeneric
from instrumation.factory import get_instrument


class TestGenericDriverRegistration(unittest.TestCase):
    """GENERIC must be a real, registered driver type -- see issue #142."""

    def test_generic_registered_in_registry(self):
        drivers = DriverRegistry.get_drivers_by_type("GENERIC")
        self.assertIn(GenericDriver, drivers)
        self.assertIn(SimulatedGeneric, drivers)

    def test_generic_driver_class_name_not_brand_specific(self):
        drivers = DriverRegistry.get_drivers_by_type("GENERIC")
        for drv_cls in drivers:
            self.assertNotIn("Keithley", drv_cls.__name__)
            self.assertNotIn("Multimeter", drv_cls.__name__)


class TestSimulatedGeneric(unittest.TestCase):
    def test_connect_and_identify(self):
        drv = SimulatedGeneric("USB0::SIM::INSTR")
        drv.connect()
        self.assertTrue(drv.connected)
        self.assertEqual(drv.get_id(), "SIM_DRIVER")

    def test_generic_has_no_typed_measurement_api(self):
        drv = SimulatedGeneric("USB0::SIM::INSTR")
        self.assertFalse(hasattr(drv, "measure_voltage"))
        self.assertFalse(hasattr(drv, "set_frequency"))


class TestGetInstrumentGeneric(unittest.TestCase):
    """get_instrument(..., "GENERIC") in SIM mode must resolve to SimulatedGeneric,
    not silently fall back to a DMM (see issue #142, item 6)."""

    def setUp(self):
        os.environ["INSTRUMATION_MODE"] = "SIM"

    def test_generic_type_resolves_to_simulated_generic(self):
        driver = get_instrument("USB::0x1234::SIM", "GENERIC")
        self.assertIsInstance(driver, SimulatedGeneric)


if __name__ == "__main__":
    unittest.main()
