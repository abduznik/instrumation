import socket
import json

# Setup UDP listener
UDP_IP = "127.0.0.1"
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print(f"Listening for instrument data on {UDP_IP}:{UDP_PORT}...")
print("-" * 50)

try:
    while True:
        data, addr = sock.recvfrom(1024)
        try:
            payload = json.loads(data.decode("utf-8"))
            
            # Simple terminal visualization
            ts = payload.get("timestamp", 0)
            val = payload.get("peak_power", 0)
            unit = payload.get("unit", "")
            
            # Create a simple bar based on the value
            # Assume range is -60 to -30 dBm
            bar_len = int((val + 60) * 2)
            bar = "#" * max(0, bar_len)
            
            print(f"[{ts:.2f}] {val:>6} {unit} | {bar}")
            
        except (json.JSONDecodeError, UnicodeDecodeError):
            print("Received malformed packet.")
except KeyboardInterrupt:
    print("\nDashboard closed.")
finally:
    sock.close()
