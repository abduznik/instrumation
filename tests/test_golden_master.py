import unittest
import os
import json
from instrumation.drivers.replay import GoldenMaster, RecordingWrapper, ReplayDriver
from instrumation.drivers.simulated import SimulatedMultimeter
from instrumation.factory import get_instrument

class TestGoldenMaster(unittest.TestCase):
    def setUp(self):
        self.test_file = "test_master.json"
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_record_and_replay(self):
        # 1. Record
        master = GoldenMaster(self.test_file)
        sim_dmm = SimulatedMultimeter("SIM_ADDR")
        wrapped = RecordingWrapper(sim_dmm, master)
        
        # Perform some actions
        wrapped.query("*IDN?")
        wrapped.write("CONF:VOLT:DC")
        wrapped.query("MEAS:VOLT?")
        
        master.save()
        
        # Verify file exists and has content
        self.assertTrue(os.path.exists(self.test_file))
        with open(self.test_file, 'r') as f:
            data = json.load(f)
            self.assertEqual(len(data), 3)
            self.assertEqual(data[0]['cmd'], "*IDN?")

        # 2. Replay
        # Using factory with replay:// protocol
        replay_instr = get_instrument(f"replay://{self.test_file}", "DMM")
        self.assertIsInstance(replay_instr, ReplayDriver)
        
        # Replay the sequence
        idn = replay_instr.get_id() # calls query("*IDN?")
        self.assertEqual(idn, data[0]['res'])
        
        replay_instr.write("CONF:VOLT:DC") # advances ptr
        self.assertEqual(replay_instr.ptr, 2)
        
        volt = replay_instr.measure_voltage() # calls query("MEAS:VOLT?")
        self.assertEqual(volt.value, float(data[2]['res']))

    def test_replay_mismatch(self):
        master = GoldenMaster(self.test_file)
        master.add("CMD1", "RES1")
        master.save()
        
        replay = ReplayDriver("DUMMY", self.test_file)
        # Call wrong command
        res = replay.query("WRONG_CMD")
        self.assertEqual(res, "0")
        # Pointer should NOT advance on mismatch in my current implementation? 
        # Actually, it doesn't advance.
        self.assertEqual(replay.ptr, 0)

if __name__ == "__main__":
    unittest.main()
