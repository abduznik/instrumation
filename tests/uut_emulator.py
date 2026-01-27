import os
import pty
import time
import threading

class UUTEmulator:
    """
    Simulates a hardware device on a pseudo-terminal (PTY).
    """
    def __init__(self):
        # Create a pseudo-terminal pair
        self.master, self.slave = pty.openpty()
        self.s_name = os.ttyname(self.slave)
        self.running = True
        print(f"[Emulator] UUT running on {self.s_name}")
        
        # Start the listener thread
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()

    def get_port(self):
        return self.s_name

    def _run(self):
        """Echo loop or protocol simulation"""
        while self.running:
            try:
                # Read command (blocking)
                cmd = os.read(self.master, 1024)
                if not cmd:
                    break
                
                cmd_str = cmd.decode('utf-8').strip()
                # print(f"[Emulator] Received: {cmd_str}")

                # Simple Protocol Logic
                response = b""
                if cmd_str == "*IDN?":
                    response = b"AcmeCorp,SuperUUT,SN12345,v1.0\n"
                elif cmd_str == "DC_ON":
                    response = b"OK: DC Power ON\n"
                elif cmd_str == "DC_OFF":
                    response = b"OK: DC Power OFF\n"
                else:
                    response = b"ERR: Unknown Command\n"

                os.write(self.master, response)
            except OSError:
                break

    def stop(self):
        self.running = False
        os.close(self.master)
        os.close(self.slave)

if __name__ == "__main__":
    emu = UUTEmulator()
    print("Press Ctrl+C to stop...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        emu.stop()
