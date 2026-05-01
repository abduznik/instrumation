import asyncio
import json
import socket
import logging
import websockets
from typing import Set

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("vfp_bridge")

class VFPBridge:
    """
    Relays UDP JSON packets to connected WebSocket clients.
    Useful for bridging Instrumation DataBroadcaster to a web dashboard.
    """
    def __init__(self, udp_host="127.0.0.1", udp_port=5005, ws_host="127.0.0.1", ws_port=8080):
        self.udp_host = udp_host
        self.udp_port = udp_port
        self.ws_host = ws_host
        self.ws_port = ws_port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()

    async def ws_handler(self, websocket):
        """Manages WebSocket client connections."""
        logger.info(f"New dashboard client connected from {websocket.remote_address}")
        self.clients.add(websocket)
        try:
            async for _ in websocket:
                # We don't expect messages from the dashboard, but keep connection alive
                pass
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)
            logger.info(f"Dashboard client disconnected")

    async def udp_listener(self):
        """Listens for UDP packets and broadcasts them to all WebSocket clients."""
        # Create a non-blocking UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.udp_host, self.udp_port))
        sock.setblocking(False)
        
        logger.info(f"Listening for UDP packets on {self.udp_host}:{self.udp_port}")
        
        loop = asyncio.get_running_loop()
        while True:
            try:
                data, addr = await loop.sock_recvfrom(sock, 65535)
                try:
                    payload = data.decode("utf-8")
                    # Validate JSON (optional but good for bridge stability)
                    json.loads(payload)
                    
                    if self.clients:
                        # Broadcast to all connected WebSocket clients
                        logger.debug(f"Broadcasting data to {len(self.clients)} clients")
                        websockets.broadcast(self.clients, payload)
                except Exception as e:
                    logger.error(f"Failed to process packet from {addr}: {e}")
            except Exception as e:
                logger.error(f"UDP Error: {e}")
                await asyncio.sleep(1)

    async def start(self):
        """Starts both the WebSocket server and the UDP listener."""
        ws_server = websockets.serve(self.ws_handler, self.ws_host, self.ws_port)
        logger.info(f"WebSocket server started on ws://{self.ws_host}:{self.ws_port}")
        
        await asyncio.gather(
            ws_server,
            self.udp_listener()
        )

if __name__ == "__main__":
    bridge = VFPBridge()
    try:
        asyncio.run(bridge.start())
    except KeyboardInterrupt:
        logger.info("Bridge stopped by user.")
