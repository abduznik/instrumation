"""
Example: Spectrum Analyzer Trace Extraction
Pulls a clean Python list of data points from the SA.
"""
import os
import sys

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from instrumation import connect_instrument

def main():
    print("--- SA Trace Extraction Demo ---")
    
    with connect_instrument("AUTO", "SA") as sa:
        sa.set_center_freq(1.5e9)
        sa.set_span(100e6)
        sa.set_rbw(100e3)
        
        print("Acquiring Trace...")
        result = sa.get_trace_data()
        
        print(f"Captured {len(result.value)} points.")
        print(f"Max Amplitude: {max(result.value)} {result.unit}")
        print(f"Min Amplitude: {min(result.value)} {result.unit}")
        
        print("\nTrace Preview (First 10 points):")
        print(result.value[:10])

if __name__ == "__main__":
    main()
