"""WebSocket server for real-time dashboard updates."""

import asyncio
import json
from typing import Optional
import websockets
from websockets import serve, ConnectionClosed

from .state import get_state_manager
from .config import get_config
from .executor import ShellExecutor
from datetime import datetime


class WebSocketServer:
    """WebSocket server for dashboard communication."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8766):
        self.host = host
        self.port = port
        self.state_manager = get_state_manager()
        self._server: Optional[websockets.WebSocketServer] = None

        # Create executor for command execution
        config = get_config()
        self.executor = ShellExecutor(
            guardrails=config.guardrails,
            log_handler=lambda level, msg: asyncio.create_task(
                self.state_manager.log(level, msg, "websocket-executor")
            )
        )

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

        elif msg_type == "run_command":
            command = data.get("command")
            cwd = data.get("cwd", ".")
            if command:
                try:
                    result = await self.executor.execute(command, cwd)
                    await self.state_manager.add_command({
                        "command": command,
                        "cwd": cwd,
                        "status": result.status.value,
                        "exit_code": result.exit_code,
                        "timestamp": datetime.now().isoformat()
                    })
                    await websocket.send(json.dumps({
                        "type": "command_result",
                        "status": result.status.value,
                        "exit_code": result.exit_code,
                        "stdout": result.stdout[:1000] if result.stdout else "",
                        "stderr": result.stderr[:500] if result.stderr else ""
                    }))
                except Exception as e:
                    await self.state_manager.log("ERROR", f"Command execution error: {str(e)}")
                    await websocket.send(json.dumps({
                        "type": "command_error",
                        "error": str(e)
                    }))

        elif msg_type == "stop_service":
            service_id = data.get("service_id")
            if service_id:
                success = self.executor.process_manager.stop_process(service_id)
                if success:
                    await self.state_manager.remove_service(service_id)
                await websocket.send(json.dumps({
                    "type": "service_stopped",
                    "success": success,
                    "service_id": service_id
                }))

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
