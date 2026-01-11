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
from .plugins import get_plugin_manager
from .plugins.detector import PluginDetector
from .plugins.health_monitor import PluginHealthMonitor
from .templates.extension_creator import ExtensionCreator
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
        # Check client count and log warning if too many
        client_count = len(self.state_manager.clients)
        if client_count >= 5:
            await self.state_manager.log(
                "WARN",
                f"High number of WebSocket clients connected: {client_count}. Consider closing unused browser tabs."
            )

        await self.state_manager.add_client(websocket)
        await self.state_manager.log("INFO", f"Dashboard client connected from {websocket.remote_address} (total: {len(self.state_manager.clients)})")

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
            await self.state_manager.log("INFO", f"Dashboard client disconnected (remaining: {len(self.state_manager.clients)})")

    async def handle_message(self, websocket, data: dict):
        """Handle incoming WebSocket messages."""
        msg_type = data.get("type")

        try:
            await self._handle_message_internal(websocket, data, msg_type)
        except Exception as e:
            await self.state_manager.log("ERROR", f"Error handling message type '{msg_type}': {str(e)}")
            import traceback
            traceback.print_exc()

    async def _handle_message_internal(self, websocket, data: dict, msg_type: str):
        """Internal message handler with error handling."""
        if msg_type == "get_state":
            # Fetch workspace data
            try:
                workspace_summary = self.workspace_manager.get_workspace_summary()
                await self.state_manager.set_workspace(workspace_summary)
            except Exception as e:
                await self.state_manager.log("ERROR", f"Failed to get workspace: {e}")

            state_dict = await self.state_manager._get_state_dict()
            await websocket.send(json.dumps({
                "type": "state",
                "data": state_dict
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
                        intent = await nlp_service.parse_natural_language(command, cwd)

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

        elif msg_type == "clear_logs":
            await self.state_manager.clear_logs()
            await websocket.send(json.dumps({"type": "logs_cleared", "success": True}))

        elif msg_type == "save_command":
            command = data.get("command")
            cwd = data.get("cwd", ".")
            name = data.get("name")
            description = data.get("description")

            if command and name:
                import uuid
                command_data = {
                    "id": str(uuid.uuid4()),
                    "name": name,
                    "command": command,
                    "cwd": cwd,
                    "description": description,
                    "created_at": datetime.now().isoformat()
                }
                await self.state_manager.add_saved_command(command_data)
                await websocket.send(json.dumps({
                    "type": "command_saved",
                    "success": True,
                    "command": command_data
                }))

        elif msg_type == "delete_saved_command":
            command_id = data.get("id")
            if command_id:
                await self.state_manager.remove_saved_command(command_id)
                await websocket.send(json.dumps({
                    "type": "command_deleted",
                    "success": True,
                    "id": command_id
                }))

        elif msg_type == "list_plugins":
            plugin_manager = get_plugin_manager()
            plugins = await plugin_manager.list_installed()
            await websocket.send(json.dumps({
                "type": "plugins",
                "data": [p.model_dump(mode="json") for p in plugins]
            }))

        elif msg_type == "install_plugin":
            git_url = data.get("git_url")
            if git_url:
                plugin_manager = get_plugin_manager()
                result = await plugin_manager.install(git_url)
                await websocket.send(json.dumps({
                    "type": "plugin_installed",
                    "success": result.success,
                    "message": result.message,
                    "error": result.error
                }))
                if result.success:
                    await self.state_manager.log("INFO", f"Plugin installed: {result.message}")

        elif msg_type == "uninstall_plugin":
            plugin_id = data.get("plugin_id")
            if plugin_id:
                plugin_manager = get_plugin_manager()
                result = await plugin_manager.uninstall(plugin_id)
                await websocket.send(json.dumps({
                    "type": "plugin_uninstalled",
                    "success": result.success,
                    "message": result.message
                }))
                if result.success:
                    await self.state_manager.log("INFO", f"Plugin uninstalled: {result.message}")

        elif msg_type == "toggle_plugin":
            plugin_id = data.get("plugin_id")
            enabled = data.get("enabled")
            if plugin_id is not None and enabled is not None:
                plugin_manager = get_plugin_manager()
                success = await plugin_manager.toggle(plugin_id, enabled)
                await websocket.send(json.dumps({
                    "type": "plugin_toggled",
                    "success": success
                }))
                if success:
                    await self.state_manager.log("INFO", f"Plugin {'enabled' if enabled else 'disabled'}")

        elif msg_type == "toggle_plugin_tool":
            plugin_id = data.get("plugin_id")
            tool_name = data.get("tool_name")
            enabled = data.get("enabled")
            if plugin_id and tool_name and enabled is not None:
                plugin_manager = get_plugin_manager()
                success = await plugin_manager.toggle_tool(plugin_id, tool_name, enabled)
                await websocket.send(json.dumps({
                    "type": "plugin_tool_toggled",
                    "success": success
                }))
                if success:
                    await self.state_manager.log("INFO", f"Tool {tool_name} {'enabled' if enabled else 'disabled'}")

        elif msg_type == "detect_plugins":
            try:
                detector = PluginDetector()
                plugins = await detector.detect_installed_plugins()
                await self.state_manager.log("INFO", f"Detected {len(plugins)} installed MCP servers")
                await websocket.send(json.dumps({
                    "type": "detected_plugins",
                    "data": plugins
                }))
            except Exception as e:
                await self.state_manager.log("ERROR", f"Failed to detect plugins: {str(e)}")
                await websocket.send(json.dumps({
                    "type": "detected_plugins",
                    "data": [],
                    "error": str(e)
                }))

        elif msg_type == "check_plugin_health":
            plugin_id = data.get("plugin_id")
            if plugin_id:
                try:
                    detector = PluginDetector()
                    plugins = await detector.detect_installed_plugins()
                    plugin_info = next((p for p in plugins if p['id'] == plugin_id), None)

                    if plugin_info:
                        monitor = PluginHealthMonitor()
                        health = await monitor.check_plugin_health(plugin_info)
                        await self.state_manager.log("INFO", f"Health check for {plugin_id}: {health.status.value}")
                        await websocket.send(json.dumps({
                            "type": "plugin_health",
                            "data": health.to_dict()
                        }))
                    else:
                        await websocket.send(json.dumps({
                            "type": "plugin_health",
                            "data": None,
                            "error": f"Plugin '{plugin_id}' not found"
                        }))
                except Exception as e:
                    await self.state_manager.log("ERROR", f"Failed to check plugin health: {str(e)}")
                    await websocket.send(json.dumps({
                        "type": "plugin_health",
                        "data": None,
                        "error": str(e)
                    }))

        elif msg_type == "check_all_plugins_health":
            try:
                detector = PluginDetector()
                plugins = await detector.detect_installed_plugins()
                monitor = PluginHealthMonitor()
                health_checks = await monitor.check_all_plugins_health(plugins)

                health_data = [health.to_dict() for health in health_checks]
                await self.state_manager.log("INFO", f"Checked health of {len(health_data)} plugins")
                await websocket.send(json.dumps({
                    "type": "all_plugins_health",
                    "data": health_data
                }))
            except Exception as e:
                await self.state_manager.log("ERROR", f"Failed to check all plugins health: {str(e)}")
                await websocket.send(json.dumps({
                    "type": "all_plugins_health",
                    "data": [],
                    "error": str(e)
                }))

        elif msg_type == "configure_nlp":
            # Configure NLP settings
            config = data.get("config")
            if config:
                try:
                    nlp_service = get_nlp_service()
                    await nlp_service.update_config(config)
                    await self.state_manager.log("INFO", f"NLP configured with provider: {config.get('primary_provider')}")
                    await websocket.send(json.dumps({
                        "type": "nlp_configured",
                        "success": True
                    }))
                except Exception as e:
                    await self.state_manager.log("ERROR", f"Failed to configure NLP: {str(e)}")
                    await websocket.send(json.dumps({
                        "type": "nlp_configured",
                        "success": False,
                        "error": str(e)
                    }))

        elif msg_type == "test_nlp_provider":
            # Test NLP provider connection
            provider_name = data.get("provider")
            try:
                nlp_service = get_nlp_service()
                test_results = await nlp_service.test_connection()

                if provider_name:
                    # Test specific provider
                    result = test_results.get(provider_name, False)
                    await websocket.send(json.dumps({
                        "type": "nlp_provider_tested",
                        "provider": provider_name,
                        "success": result
                    }))
                else:
                    # Test all providers
                    await websocket.send(json.dumps({
                        "type": "nlp_providers_tested",
                        "results": test_results
                    }))
            except Exception as e:
                await self.state_manager.log("ERROR", f"Failed to test NLP provider: {str(e)}")
                await websocket.send(json.dumps({
                    "type": "nlp_provider_tested",
                    "success": False,
                    "error": str(e)
                }))

        elif msg_type == "get_nlp_config":
            # Get current NLP configuration
            try:
                nlp_service = get_nlp_service()
                config = nlp_service.get_config()
                await websocket.send(json.dumps({
                    "type": "nlp_config",
                    "config": config
                }))
            except Exception as e:
                await self.state_manager.log("ERROR", f"Failed to get NLP config: {str(e)}")
                await websocket.send(json.dumps({
                    "type": "nlp_config",
                    "error": str(e)
                }))

        elif msg_type == "get_nlp_status":
            # Get NLP providers status
            try:
                nlp_service = get_nlp_service()
                status = nlp_service.get_status()
                await websocket.send(json.dumps({
                    "type": "nlp_status",
                    "status": status
                }))
            except Exception as e:
                await self.state_manager.log("ERROR", f"Failed to get NLP status: {str(e)}")
                await websocket.send(json.dumps({
                    "type": "nlp_status",
                    "error": str(e)
                }))

        elif msg_type == "execute_tool":
            # Execute MCP tools (extensions creation, etc.)
            tool_name = data.get("tool")
            arguments = data.get("arguments", {})

            if not tool_name:
                await websocket.send(json.dumps({
                    "type": "tool_result",
                    "success": False,
                    "error": "Tool name is required"
                }))
                return

            try:
                extension_creator = ExtensionCreator()

                if tool_name == "create_widget":
                    result = extension_creator.create_widget(
                        name=arguments["name"],
                        description=arguments.get("description", "A custom widget"),
                        author=arguments.get("author", "Anonymous"),
                        category=arguments.get("category", "utility"),
                        template_type=arguments.get("template_type", "basic"),
                    )
                    await self.state_manager.log("INFO", f"Created widget: {arguments['name']}")
                    await websocket.send(json.dumps({
                        "type": "tool_result",
                        "success": True,
                        "data": result
                    }))

                elif tool_name == "create_workflow":
                    result = extension_creator.create_workflow(
                        name=arguments["name"],
                        description=arguments.get("description", "A custom workflow"),
                        author=arguments.get("author", "User"),
                        version=arguments.get("version", "1.0.0"),
                    )
                    await self.state_manager.log("INFO", f"Created workflow: {arguments['name']}")
                    await websocket.send(json.dumps({
                        "type": "tool_result",
                        "success": True,
                        "data": {"workflow_path": result}
                    }))

                elif tool_name == "create_integration":
                    result = extension_creator.create_integration(
                        name=arguments["name"],
                        service_type=arguments.get("service_type", "custom"),
                        config=arguments.get("config", {}),
                    )
                    await self.state_manager.log("INFO", f"Created integration: {arguments['name']}")
                    await websocket.send(json.dumps({
                        "type": "tool_result",
                        "success": True,
                        "data": result
                    }))

                else:
                    await websocket.send(json.dumps({
                        "type": "tool_result",
                        "success": False,
                        "error": f"Unknown tool: {tool_name}"
                    }))

            except Exception as e:
                await self.state_manager.log("ERROR", f"Failed to execute tool {tool_name}: {str(e)}")
                await websocket.send(json.dumps({
                    "type": "tool_result",
                    "success": False,
                    "error": str(e)
                }))

        elif msg_type == "ping":
            await websocket.send(json.dumps({"type": "pong"}))
    
    async def cleanup_dead_connections(self):
        """Periodically ping clients and remove dead connections."""
        while True:
            await asyncio.sleep(30)  # Check every 30 seconds

            dead_clients = []
            for client in list(self.state_manager.clients):
                try:
                    # Send ping to check if connection is alive
                    pong = await asyncio.wait_for(
                        client.ping(),
                        timeout=5.0
                    )
                    await pong  # Wait for pong response
                except Exception:
                    # Connection is dead, mark for removal
                    dead_clients.append(client)

            # Remove dead clients
            for client in dead_clients:
                self.state_manager.remove_client(client)
                await self.state_manager.log("INFO", f"Removed dead WebSocket connection (remaining: {len(self.state_manager.clients)})")

    async def start(self):
        """Start the WebSocket server."""
        self._server = await serve(
            self.handler,
            self.host,
            self.port
        )
        await self.state_manager.log("INFO", f"WebSocket server started on ws://{self.host}:{self.port}")

        # Start background task to cleanup dead connections
        asyncio.create_task(self.cleanup_dead_connections())
    
    async def stop(self):
        """Stop the WebSocket server."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()


async def run_websocket_server():
    """Run the WebSocket server standalone."""
    config = get_config()
    server = WebSocketServer(config.host, config.websocket_port)

    # Initialize database
    await server.state_manager.initialize_db()

    await server.start()
    
    # Keep running
    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(run_websocket_server())
