"""WebSocket server for real-time dashboard updates."""

import asyncio
import json
from typing import Optional
import websockets
from websockets import serve, ConnectionClosed

from .state import get_state_manager
from .config import get_config
from .executor import ShellExecutor
from .nlp_service import get_nlp_service
from .workspace_manager import WorkspaceManager
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

        # Create workspace manager
        self.workspace_manager = WorkspaceManager()

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
            # Fetch workspace data
            try:
                workspace_summary = self.workspace_manager.get_workspace_summary()
                await self.state_manager.set_workspace(workspace_summary)
            except Exception as e:
                await self.state_manager.log("ERROR", f"Failed to get workspace: {e}")

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
            use_nlp = data.get("use_nlp", False)

            if command:
                try:
                    # If NLP is enabled, translate natural language to command
                    if use_nlp:
                        nlp_service = get_nlp_service()
                        intent = await nlp_service.parse_natural_language(command)

                        await self.state_manager.log(
                            "INFO",
                            f"NLP: '{command}' -> {intent.type} (confidence: {intent.confidence:.2f})"
                        )

                        # Handle different intent types
                        if intent.type == "shell":
                            # Execute as shell command
                            command = intent.command
                        elif intent.type in ["detect_project", "start_service", "stop_service", "git_status", "list_services", "run_tests", "check_ports"]:
                            # MCP tool - inform user to use MCP server
                            await websocket.send(json.dumps({
                                "type": "command_result",
                                "status": "info",
                                "exit_code": 0,
                                "stdout": f"Detected MCP tool request: {intent.type}\nParameters: {intent.parameters}\nPlease use the MCP server to execute this tool.",
                                "stderr": ""
                            }))
                            return
                        else:
                            # Unknown intent - fallback to shell
                            await self.state_manager.log("WARN", f"Unknown intent type: {intent.type}, treating as shell")
                            command = intent.command

                    # Execute command
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

        elif msg_type == "switch_project":
            repo_name = data.get("repo_name")
            if repo_name:
                try:
                    # Find the repo
                    repo = self.workspace_manager.find_repo_by_name(repo_name)
                    if repo:
                        # Import here to avoid issues
                        import os
                        from .detector import ProjectDetector

                        # Change directory
                        os.chdir(repo.path)

                        # Detect project
                        detector = ProjectDetector(repo.path)
                        profile = detector.detect()

                        # Update state
                        await self.state_manager.set_project(profile)
                        await self.state_manager.log("INFO", f"Switched to project: {repo_name}")

                        await websocket.send(json.dumps({
                            "type": "project_switched",
                            "success": True,
                            "project": profile.model_dump(mode='json')
                        }))
                    else:
                        await websocket.send(json.dumps({
                            "type": "project_switched",
                            "success": False,
                            "error": f"Repository '{repo_name}' not found"
                        }))
                except Exception as e:
                    await self.state_manager.log("ERROR", f"Failed to switch project: {str(e)}")
                    await websocket.send(json.dumps({
                        "type": "project_switched",
                        "success": False,
                        "error": str(e)
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
