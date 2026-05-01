from instrumation.drivers.simulated import SimulatedSignalGenerator

def test_sg_upgrade():
    print("Testing SignalGenerator Upgrade in Simulation Mode...")
    sg = SimulatedSignalGenerator("SIM::SG::1")
    sg.connect()
    
    print("\n--- Basic RF Controls ---")
    sg.set_frequency(100e6)
    sg.set_amplitude(-5.0)
    sg.set_output(True)
    sg.set_alc(False)
    
    print("\n--- Modulation Controls ---")
    sg.set_am_state(True)
    sg.set_am_depth(50.0)
    sg.set_fm_state(True)
    sg.set_fm_deviation(10e3)
    sg.set_fm_source("INT")
    
    print("\n--- Hardware Sweep Controls ---")
    sg.set_sweep_mode("STEP")
    sg.set_sweep_start_freq(100e6)
    sg.set_sweep_stop_freq(200e6)
    sg.set_sweep_points(101)
    sg.set_sweep_dwell(0.1)
    sg.trigger_sweep()
    
    sg.disconnect()
    print("\nTest Complete!")

if __name__ == "__main__":
    test_sg_upgrade()
