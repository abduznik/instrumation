"""
Example: Oscilloscope Screenshot Automation
Captures the display buffer and saves it as a local file.
"""
import os
import sys

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from instrumation import connect_instrument

def main():
    print("--- SCOPE Screenshot Demo ---")
    
    # Use AUTO discovery
    with connect_instrument("AUTO", "SCOPE") as scope:
        print("Auto-scaling signal...")
        scope.auto_scale()
        
        print("Capturing Screenshot...")
        raw_bytes = scope.get_screenshot()
        
        filename = "scope_capture.png"
        with open(filename, "wb") as f:
            f.write(raw_bytes)
            
        print(f"Success! Saved {len(raw_bytes)} bytes to {filename}")

if __name__ == "__main__":
    main()
