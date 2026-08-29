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

    def test_measure_voltage_actual_delegates_to_replay(self):
        master = GoldenMaster(self.test_file)
        master.add("MEAS:VOLT?", "4.567")   # recorded voltage = 4.567 V
        master.save()

    
        replay = ReplayDriver("DUMMY_ADDR", self.test_file)

        result = replay.measure_voltage_actual()

        self.assertAlmostEqual(result.value, 4.567, places=3,
            msg="measure_voltage_actual() must return the replayed value, not hardcoded 0.0")
        self.assertEqual(result.unit, "V",
            msg="Unit must be 'V'")

    def test_getters_read_from_master_not_hardcoded(self):
        # #130: getters that used to return hardcoded defaults must read the
        # recorded golden-master responses instead.
        master = GoldenMaster(self.test_file)
        master.add(":OUTP?", "ON")
        master.add(":MEAS:DUTY?", "45.2")
        master.add(":MEAS:VPP?", "1.5")
        master.add(":TRAC?", "0.5,0.6,0.7")
        master.add(":WAV:DATA?", "1.0,2.0")
        master.add(":CALC:DATA:FDATA?", "0.1,0.2,0.3,0.4")
        master.save()

        replay = ReplayDriver("DUMMY", self.test_file)

        self.assertTrue(replay.get_output(),
            msg="get_output() must replay the recorded ON state")
        self.assertAlmostEqual(replay.measure_duty_cycle().value, 45.2,
            msg="measure_duty_cycle() must replay the recorded value")
        self.assertAlmostEqual(replay.measure_v_peak_to_peak().value, 1.5,
            msg="measure_v_peak_to_peak() must replay the recorded value")
        self.assertEqual(replay.get_trace_data().value, [0.5, 0.6, 0.7],
            msg="get_trace_data() must replay the recorded trace")
        self.assertEqual(replay.get_waveform(1).value, [1.0, 2.0],
            msg="get_waveform() must replay the recorded waveform")
        self.assertEqual(replay.get_complex_trace().value, [complex(0.1, 0.2), complex(0.3, 0.4)],
            msg="get_complex_trace() must replay recorded (re, im) pairs")

    def test_unrecorded_getters_fall_back_to_defaults(self):
        # #130: methods whose commands were never recorded still return
        # sensible defaults (the previous hardcoded behaviour).
        master = GoldenMaster(self.test_file)
        master.save()  # empty master

        replay = ReplayDriver("DUMMY", self.test_file)

        self.assertFalse(replay.get_output())
        self.assertEqual(replay.measure_duty_cycle().value, 0.0)
        self.assertEqual(replay.measure_v_peak_to_peak().value, 0.0)
        self.assertEqual(replay.get_trace_data().value, [0.0])
        self.assertEqual(replay.get_smith_data().value, [complex(50, 0)])


if __name__ == "__main__":
    unittest.main()