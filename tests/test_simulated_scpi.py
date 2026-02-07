import sys
from unittest.mock import MagicMock

# Mock dependencies
sys.modules["serial"] = MagicMock()
sys.modules["serial.tools"] = MagicMock()
sys.modules["serial.tools.list_ports"] = MagicMock()
sys.modules["pyvisa"] = MagicMock()

import unittest
import time
from instrumation.drivers.simulated import SimulatedMultimeter

class TestSimulatedSCPI(unittest.TestCase):
    def test_idn_query(self):
        driver = SimulatedMultimeter("USB::SIM::DMM", latency=0)
        res = driver.query("*IDN?")
        self.assertEqual(res, "SIM_DMM_X1000")

    def test_opc_query(self):
        driver = SimulatedMultimeter("USB::SIM::DMM", latency=0)
        res = driver.query("*OPC?")
        self.assertEqual(res, "1")

    def test_latency(self):
        latency = 0.1
        driver = SimulatedMultimeter("USB::SIM::DMM", latency=latency)
        
        start_time = time.time()
        driver.query("*OPC?")
        end_time = time.time()
        
        duration = end_time - start_time
        self.assertGreaterEqual(duration, latency)

    def test_unknown_command(self):
        driver = SimulatedMultimeter("USB::SIM::DMM", latency=0)
        res = driver.query("UNKNOWN?")
        self.assertEqual(res, "0")

if __name__ == "__main__":
    unittest.main()
