from instrumation.drivers.simulated import (
    SimulatedSignalGenerator, 
    SimulatedSpectrumAnalyzer, 
    SimulatedOscilloscope
)

def test_expanded_hal():
    print("Testing Expanded HAL in Simulation Mode...")
    
    print("\n--- Testing Housekeeping (SG) ---")
    sg = SimulatedSignalGenerator("SIM::SG::1")
    sg.connect()
    sg.reset()
    sg.clear()
    sg.wait_until_complete()
    sg.check_errors()
    
    print("\n--- Testing New SG Methods ---")
    sg.set_reference_clock("EXT")
    sg.trigger_sweep()
    
    print("\n--- Testing New SA Methods ---")
    sa = SimulatedSpectrumAnalyzer("SIM::SA::1")
    sa.connect()
    sa.set_span(100e6)
    sa.set_rbw(10e3)
    sa.set_vbw(3e3)
    
    print("\n--- Testing New SCOPE Methods ---")
    scope = SimulatedOscilloscope("SIM::SCOPE::1")
    scope.connect()
    scope.set_auto_scale()
    screenshot = scope.get_screenshot()
    print(f"Captured {len(screenshot)} bytes of screenshot data")
    
    print("\nVerification Complete!")

if __name__ == "__main__":
    test_expanded_hal()
