"""
Example: Rigol DS1054Z Waveform Acquisition
Captures a calibrated waveform from channel 1 and plots it with matplotlib.

Usage:
    python rigol_ds1054z_waveform.py

Connect via USB-TMC (direct) or LAN:
    USB0::0x1AB1::0x04CE::DS1054Z::INSTR
    TCPIP::192.168.1.100::INSTR
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from instrumation import connect_instrument


def main():
    print("--- Rigol DS1054Z Waveform Acquisition ---")

    with connect_instrument("AUTO", "SCOPE") as scope:
        idn = scope.get_id()
        print(f"Connected: {idn}")

        # Configure channel 1
        scope.set_channel_display(1, True)
        scope.set_channel_coupling(1, "DC")
        scope.set_channel_scale(1, 0.5)       # 500 mV/div
        scope.set_channel_offset(1, 0.0)
        scope.set_channel_probe(1, 10.0)      # 10x probe

        # Set timebase: 1 ms/div
        scope.set_timebase_scale(1e-3)

        # Edge trigger on channel 1, rising slope, 1.0 V
        scope.set_trigger("CHANnel1", 1.0, "POSITIVE")
        scope.set_trigger_sweep("AUTO")

        # Auto-scale and wait
        scope.auto_scale()

        # Capture a single acquisition
        print("Capturing waveform...")
        scope.single()
        scope.wait_ready()

        # Read calibrated waveform
        result = scope.get_waveform(1)
        time_arr, volt_arr = result.value

        print(f"  Points:   {len(time_arr)}")
        print(f"  Vmin:     {min(volt_arr):.4f} V")
        print(f"  Vmax:     {max(volt_arr):.4f} V")
        print(f"  Duration: {time_arr[-1] - time_arr[0]:.6f} s")

        # Optionally plot with matplotlib
        try:
            import matplotlib.pyplot as plt

            plt.figure(figsize=(10, 4))
            plt.plot(time_arr * 1e3, volt_arr, linewidth=0.8)
            plt.xlabel("Time (ms)")
            plt.ylabel("Voltage (V)")
            plt.title("Rigol DS1054Z — Channel 1")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig("rigol_waveform.png", dpi=150)
            print("  Saved plot to rigol_waveform.png")
        except ImportError:
            print("  (matplotlib not installed — skipping plot)")


if __name__ == "__main__":
    main()
