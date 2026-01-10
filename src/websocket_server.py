"""WebSocket server for real-time dashboard updates."""

import asyncio
import json
from typing import Optional
import websockets
from websockets import serve, ConnectionClosed

from .state import get_state_manager
from .config import get_config


class WebSocketServer:
    """WebSocket server for dashboard communication."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8766):
        self.host = host
        self.port = port
        self.state_manager = get_state_manager()
        self._server: Optional[websockets.WebSocketServer] = None

    async def handler(self, websocket):
        """Handle WebSocket connections."""
        await self.state_manager.add_client(websocket)
        await self.state_manager.log("INFO", f"Dashboard client connected from {websocket.remote_address}")

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(websocket, data)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({"error": "Invalid JSON"}))
        except ConnectionClosed:
            pass
        finally:
            self.state_manager.remove_client(websocket)
            await self.state_manager.log("INFO", "Dashboard client disconnected")

    async def handle_message(self, websocket, data: dict):
        """Handle incoming WebSocket messages."""
        msg_type = data.get("type")
        
        if msg_type == "get_state":
            await websocket.send(json.dumps({
                "type": "state",
                "data": self.state_manager.state.to_dict()
            }))
        
        elif msg_type == "approve":
            approval_id = data.get("approval_id")
            # Import here to avoid circular import
            from .server import approval_futures
            if approval_id in approval_futures:
                approval_futures[approval_id].set_result(True)
                await websocket.send(json.dumps({"type": "approved", "id": approval_id}))
        
        elif msg_type == "reject":
            approval_id = data.get("approval_id")
            from .server import approval_futures
            if approval_id in approval_futures:
                approval_futures[approval_id].set_result(False)
                await websocket.send(json.dumps({"type": "rejected", "id": approval_id}))
        
        elif msg_type == "ping":
            await websocket.send(json.dumps({"type": "pong"}))
    
    async def start(self):
        """Start the WebSocket server."""
        self._server = await serve(
            self.handler,
            self.host,
            self.port
        )
        await self.state_manager.log("INFO", f"WebSocket server started on ws://{self.host}:{self.port}")
    
    async def stop(self):
        """Stop the WebSocket server."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()


async def run_websocket_server():
    """Run the WebSocket server standalone."""
    config = get_config()
    server = WebSocketServer(config.host, config.websocket_port)
    await server.start()
    
    # Keep running
    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(run_websocket_server())
