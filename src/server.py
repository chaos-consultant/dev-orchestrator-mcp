"""Main MCP server for dev-orchestrator."""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolResult,
)

from .config import get_config, ProjectProfile
from .detector import ProjectDetector
from .executor import ShellExecutor, PendingApproval, CommandStatus
from .notifications import get_notifier
from .state import get_state_manager, ServiceInfo
from .workspace_manager import WorkspaceManager
from .plugins import get_plugin_manager


# Initialize components
server = Server("dev-orchestrator")
state_manager = get_state_manager()
notifier = get_notifier()
executor: Optional[ShellExecutor] = None
current_detector: Optional[ProjectDetector] = None
workspace_manager: Optional[WorkspaceManager] = None

# Pending approval futures
approval_futures: dict[str, asyncio.Future] = {}


async def approval_handler(pending: PendingApproval) -> bool:
    """Handle approval requests by waiting for user response."""
    # Notify user
    await notifier.notify_approval_required(pending.command, pending.reason)
    
    # Broadcast to dashboard
    await state_manager.add_pending_approval({
        "id": pending.id,
        "command": pending.command,
        "cwd": pending.cwd,
        "reason": pending.reason,
        "requested_at": pending.requested_at.isoformat()
    })
    
    # Create a future to wait for approval
    future = asyncio.get_event_loop().create_future()
    approval_futures[pending.id] = future
    
    try:
        # Wait for approval (with timeout)
        result = await asyncio.wait_for(future, timeout=300)  # 5 minute timeout
        return result
    except asyncio.TimeoutError:
        await state_manager.log("WARN", f"Approval timeout for: {pending.command}")
        return False
    finally:
        approval_futures.pop(pending.id, None)
        await state_manager.remove_pending_approval(pending.id)


def log_handler(level: str, message: str):
    """Handle log messages."""
    asyncio.create_task(state_manager.log(level, message, "executor"))


def init_executor():
    """Initialize the shell executor."""
    global executor
    config = get_config()
    executor = ShellExecutor(
        guardrails=config.guardrails,
        approval_handler=approval_handler,
        log_handler=log_handler
    )


# Define MCP tools
@server.list_tools()
async def list_tools():
    """List available tools."""
    return [
        Tool(
            name="detect_project",
            description="Detect project type and configuration from the current or specified directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Project directory path (defaults to current directory)"
                    }
                }
            }
        ),
        Tool(
            name="run_command",
            description="Execute a shell command with guardrails. Commands matching dangerous patterns require approval.",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command to execute"
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory (defaults to current project)"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default 300)"
                    },
                    "background": {
                        "type": "boolean",
                        "description": "Run in background (for long-running services)"
                    }
                },
                "required": ["command"]
            }
        ),
        Tool(
            name="start_service",
            description="Start a dev service (backend, frontend, etc.) based on project detection",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "enum": ["backend", "frontend", "test", "all"],
                        "description": "Which service to start"
                    },
                    "port": {
                        "type": "integer",
                        "description": "Override default port"
                    }
                },
                "required": ["service"]
            }
        ),
        Tool(
            name="stop_service",
            description="Stop a running service by ID or name",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_id": {
                        "type": "string",
                        "description": "Service ID or 'all' to stop all"
                    }
                },
                "required": ["service_id"]
            }
        ),
        Tool(
            name="list_services",
            description="List all running services",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_status",
            description="Get current orchestrator status including project, services, and pending approvals",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="approve_command",
            description="Approve a pending command execution",
            inputSchema={
                "type": "object",
                "properties": {
                    "approval_id": {
                        "type": "string",
                        "description": "The approval request ID"
                    }
                },
                "required": ["approval_id"]
            }
        ),
        Tool(
            name="reject_command",
            description="Reject a pending command execution",
            inputSchema={
                "type": "object",
                "properties": {
                    "approval_id": {
                        "type": "string",
                        "description": "The approval request ID"
                    }
                },
                "required": ["approval_id"]
            }
        ),
        Tool(
            name="run_tests",
            description="Run project tests based on detected test framework",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {
                        "type": "string",
                        "description": "Test filter pattern"
                    },
                    "verbose": {
                        "type": "boolean",
                        "description": "Verbose output"
                    }
                }
            }
        ),
        Tool(
            name="git_status",
            description="Get git status for current project",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="check_ports",
            description="Check which ports are in use",
            inputSchema={
                "type": "object",
                "properties": {
                    "ports": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Specific ports to check (defaults to common dev ports)"
                    }
                }
            }
        ),
        Tool(
            name="activate_venv",
            description="Get the activation command for the project's virtual environment",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="list_workspace_repos",
            description="Discover all git repositories in the workspace with their current status",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_root": {
                        "type": "string",
                        "description": "Root directory to search (defaults to parent of current directory)"
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum directory depth to search (default: 2)"
                    }
                }
            }
        ),
        Tool(
            name="switch_project",
            description="Switch to a different project in the workspace by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Name of the repository to switch to"
                    }
                },
                "required": ["repo_name"]
            }
        ),
        Tool(
            name="workspace_status",
            description="Get summary status of all repositories in workspace (uncommitted changes, ahead/behind)",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_root": {
                        "type": "string",
                        "description": "Root directory to check (defaults to current workspace)"
                    }
                }
            }
        ),
        Tool(
            name="list_plugins",
            description="List all installed MCP server plugins with their status and tools",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="install_plugin",
            description="Install a new MCP server plugin from a git repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "git_url": {
                        "type": "string",
                        "description": "Git repository URL for the plugin"
                    }
                },
                "required": ["git_url"]
            }
        ),
        Tool(
            name="uninstall_plugin",
            description="Uninstall an MCP server plugin",
            inputSchema={
                "type": "object",
                "properties": {
                    "plugin_id": {
                        "type": "string",
                        "description": "Plugin ID to uninstall"
                    }
                },
                "required": ["plugin_id"]
            }
        ),
        Tool(
            name="toggle_plugin",
            description="Enable or disable an MCP server plugin and all its tools",
            inputSchema={
                "type": "object",
                "properties": {
                    "plugin_id": {
                        "type": "string",
                        "description": "Plugin ID to toggle"
                    },
                    "enabled": {
                        "type": "boolean",
                        "description": "True to enable, False to disable"
                    }
                },
                "required": ["plugin_id", "enabled"]
            }
        ),
        Tool(
            name="toggle_plugin_tool",
            description="Enable or disable a specific tool from a plugin",
            inputSchema={
                "type": "object",
                "properties": {
                    "plugin_id": {
                        "type": "string",
                        "description": "Plugin ID"
                    },
                    "tool_name": {
                        "type": "string",
                        "description": "Name of the tool to toggle"
                    },
                    "enabled": {
                        "type": "boolean",
                        "description": "True to enable, False to disable"
                    }
                },
                "required": ["plugin_id", "tool_name", "enabled"]
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    global current_detector, executor
    
    if executor is None:
        init_executor()
    
    try:
        if name == "detect_project":
            path = arguments.get("path", os.getcwd())
            current_detector = ProjectDetector(path)
            profile = current_detector.detect()
            await state_manager.set_project(profile)
            await notifier.notify_project_detected(profile.name, profile.project_type)
            
            result = {
                "project": profile.name,
                "path": str(profile.path),
                "types": profile.project_type,
                "venv": str(profile.venv_path) if profile.venv_path else None,
                "git_branch": profile.git_branch,
                "git_user": profile.git_user_email,
                "suggested_commands": current_detector.get_start_commands()
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "run_command":
            command = arguments["command"]
            cwd = arguments.get("cwd", os.getcwd())
            timeout = arguments.get("timeout", 300)
            background = arguments.get("background", False)
            
            result = await executor.execute(command, cwd, timeout, background=background)
            
            await state_manager.add_command({
                "command": command,
                "cwd": cwd,
                "status": result.status.value,
                "exit_code": result.exit_code,
                "timestamp": datetime.now().isoformat()
            })
            
            response = {
                "status": result.status.value,
                "exit_code": result.exit_code,
                "stdout": result.stdout[:5000] if result.stdout else "",
                "stderr": result.stderr[:2000] if result.stderr else "",
            }
            
            if result.blocked_reason:
                response["blocked_reason"] = result.blocked_reason
            if result.approval_reason:
                response["approval_reason"] = result.approval_reason
            
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
        
        elif name == "start_service":
            if current_detector is None:
                return [TextContent(type="text", text='{"error": "No project detected. Run detect_project first."}')]
            
            service = arguments["service"]
            commands = current_detector.get_start_commands()
            
            if service == "all":
                results = []
                for svc_name, cmd in commands.items():
                    result = await executor.execute(cmd, str(current_detector.path), background=True)
                    results.append({"service": svc_name, "status": result.status.value, "output": result.stdout})
                return [TextContent(type="text", text=json.dumps(results, indent=2))]
            
            if service not in commands:
                return [TextContent(type="text", text=f'{{"error": "No {service} command detected for this project"}}')]
            
            cmd = commands[service]
            port_override = arguments.get("port")
            if port_override:
                cmd = cmd.replace(f"--port {current_detector.detect().backend_port}", f"--port {port_override}")
            
            result = await executor.execute(cmd, str(current_detector.path), background=True)
            
            if result.status == CommandStatus.COMPLETED:
                profile = current_detector.detect()
                port = port_override or (profile.backend_port if service == "backend" else profile.frontend_port)
                await notifier.notify_service_started(service, port or 0)
            
            return [TextContent(type="text", text=json.dumps({
                "service": service,
                "status": result.status.value,
                "output": result.stdout
            }, indent=2))]
        
        elif name == "stop_service":
            service_id = arguments["service_id"]
            
            if service_id == "all":
                for proc_id in list(executor.process_manager.processes.keys()):
                    executor.process_manager.stop_process(proc_id)
                    await state_manager.remove_service(proc_id)
                return [TextContent(type="text", text='{"status": "all services stopped"}')]
            
            success = executor.process_manager.stop_process(service_id)
            if success:
                await state_manager.remove_service(service_id)
                await notifier.notify_service_stopped(service_id)
            
            return [TextContent(type="text", text=json.dumps({"stopped": success}))]
        
        elif name == "list_services":
            services = executor.process_manager.list_processes()
            return [TextContent(type="text", text=json.dumps(services, indent=2))]
        
        elif name == "get_status":
            status = state_manager.state.to_dict()
            return [TextContent(type="text", text=json.dumps(status, indent=2))]
        
        elif name == "approve_command":
            approval_id = arguments["approval_id"]
            if approval_id in approval_futures:
                approval_futures[approval_id].set_result(True)
                await state_manager.log("INFO", f"Approved: {approval_id}")
                return [TextContent(type="text", text='{"approved": true}')]
            return [TextContent(type="text", text='{"error": "Approval not found"}')]
        
        elif name == "reject_command":
            approval_id = arguments["approval_id"]
            if approval_id in approval_futures:
                approval_futures[approval_id].set_result(False)
                await state_manager.log("INFO", f"Rejected: {approval_id}")
                return [TextContent(type="text", text='{"rejected": true}')]
            return [TextContent(type="text", text='{"error": "Approval not found"}')]
        
        elif name == "run_tests":
            if current_detector is None:
                return [TextContent(type="text", text='{"error": "No project detected"}')]
            
            profile = current_detector.detect()
            filter_pattern = arguments.get("filter", "")
            verbose = arguments.get("verbose", False)
            
            if profile.has_pytest:
                cmd = "pytest"
                if verbose:
                    cmd += " -v"
                if filter_pattern:
                    cmd += f" -k '{filter_pattern}'"
                
                if profile.venv_path:
                    result = await executor.execute_with_venv(cmd, str(profile.path), str(profile.venv_path))
                else:
                    result = await executor.execute(cmd, str(profile.path))
            elif profile.has_node:
                pm = profile.package_manager or "npm"
                cmd = f"{pm} test"
                result = await executor.execute(cmd, str(profile.path))
            else:
                return [TextContent(type="text", text='{"error": "No test framework detected"}')]
            
            return [TextContent(type="text", text=json.dumps({
                "status": result.status.value,
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr
            }, indent=2))]
        
        elif name == "git_status":
            cwd = str(current_detector.path) if current_detector else os.getcwd()
            result = await executor.execute("git status --porcelain && git log -1 --oneline", cwd)
            
            return [TextContent(type="text", text=json.dumps({
                "status": result.status.value,
                "output": result.stdout,
                "branch": current_detector.detect().git_branch if current_detector else None
            }, indent=2))]
        
        elif name == "check_ports":
            ports = arguments.get("ports", [3000, 3333, 5173, 8000, 8080, 8765, 8766])
            ports_pattern = "|".join(map(str, ports))
            result = await executor.execute(
                f"lsof -i -P -n | grep LISTEN | grep -E ':{ports_pattern}'",
                os.getcwd()
            )
            
            return [TextContent(type="text", text=json.dumps({
                "ports_checked": ports,
                "in_use": result.stdout.strip().split('\n') if result.stdout.strip() else []
            }, indent=2))]
        
        elif name == "activate_venv":
            if current_detector is None:
                return [TextContent(type="text", text='{"error": "No project detected"}')]

            profile = current_detector.detect()
            if profile.venv_path:
                activate_cmd = f"source {profile.venv_path}/bin/activate"
                return [TextContent(type="text", text=json.dumps({
                    "venv_path": str(profile.venv_path),
                    "activate_command": activate_cmd
                }, indent=2))]

            return [TextContent(type="text", text='{"error": "No virtual environment found"}')]

        elif name == "list_workspace_repos":
            global workspace_manager

            workspace_root = arguments.get("workspace_root")
            max_depth = arguments.get("max_depth", 2)

            if workspace_manager is None or (workspace_root and workspace_root != str(workspace_manager.workspace_root)):
                workspace_manager = WorkspaceManager(workspace_root)

            repos = workspace_manager.discover_repos(max_depth=max_depth)

            await state_manager.log("INFO", f"Discovered {len(repos)} repositories in workspace")

            return [TextContent(type="text", text=json.dumps({
                "workspace_root": str(workspace_manager.workspace_root),
                "repo_count": len(repos),
                "repos": [repo.to_dict() for repo in repos]
            }, indent=2))]

        elif name == "switch_project":
            global workspace_manager, current_detector

            repo_name = arguments["repo_name"]

            if workspace_manager is None:
                workspace_manager = WorkspaceManager()

            repo = workspace_manager.find_repo_by_name(repo_name)

            if repo is None:
                available = [r.name for r in workspace_manager.discover_repos()]
                return [TextContent(type="text", text=json.dumps({
                    "error": f"Repository '{repo_name}' not found",
                    "available_repos": available
                }, indent=2))]

            # Change to the repo directory
            os.chdir(repo.path)

            # Re-detect project
            current_detector = ProjectDetector(repo.path)
            profile = current_detector.detect()
            await state_manager.set_project(profile)

            await state_manager.log("INFO", f"Switched to project: {repo_name}")
            await notifier.notify_project_detected(profile.name, profile.project_type)

            return [TextContent(type="text", text=json.dumps({
                "switched_to": repo.name,
                "path": repo.path,
                "branch": repo.branch,
                "project": profile.name,
                "types": profile.project_type
            }, indent=2))]

        elif name == "workspace_status":
            global workspace_manager

            workspace_root = arguments.get("workspace_root")

            if workspace_manager is None or (workspace_root and workspace_root != str(workspace_manager.workspace_root)):
                workspace_manager = WorkspaceManager(workspace_root)

            summary = workspace_manager.get_workspace_summary()

            await state_manager.log("INFO",
                f"Workspace status: {summary['total_repos']} repos, "
                f"{summary['repos_with_changes']} with changes"
            )

            return [TextContent(type="text", text=json.dumps(summary, indent=2))]

        elif name == "list_plugins":
            plugin_manager = get_plugin_manager()
            plugins = await plugin_manager.list_installed()

            result = {
                "total_plugins": len(plugins),
                "plugins": [p.model_dump(mode="json") for p in plugins]
            }

            await state_manager.log("INFO", f"Listed {len(plugins)} installed plugins")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "install_plugin":
            plugin_manager = get_plugin_manager()
            git_url = arguments["git_url"]

            await state_manager.log("INFO", f"Installing plugin from {git_url}")
            result = await plugin_manager.install(git_url)

            if result.success:
                await state_manager.log("INFO", f"Successfully installed plugin: {result.message}")
            else:
                await state_manager.log("ERROR", f"Plugin installation failed: {result.message}")

            return [TextContent(type="text", text=json.dumps(result.model_dump(mode="json"), indent=2))]

        elif name == "uninstall_plugin":
            plugin_manager = get_plugin_manager()
            plugin_id = arguments["plugin_id"]

            await state_manager.log("INFO", f"Uninstalling plugin {plugin_id}")
            result = await plugin_manager.uninstall(plugin_id)

            if result.success:
                await state_manager.log("INFO", f"Successfully uninstalled plugin: {result.message}")
            else:
                await state_manager.log("ERROR", f"Plugin uninstall failed: {result.message}")

            return [TextContent(type="text", text=json.dumps(result.model_dump(mode="json"), indent=2))]

        elif name == "toggle_plugin":
            plugin_manager = get_plugin_manager()
            plugin_id = arguments["plugin_id"]
            enabled = arguments["enabled"]

            success = await plugin_manager.toggle(plugin_id, enabled)
            action = "enabled" if enabled else "disabled"

            if success:
                await state_manager.log("INFO", f"Plugin {plugin_id} {action}")
                return [TextContent(type="text", text=json.dumps({
                    "success": True,
                    "message": f"Plugin {action} successfully"
                }, indent=2))]
            else:
                return [TextContent(type="text", text=json.dumps({
                    "success": False,
                    "error": "Plugin not found"
                }, indent=2))]

        elif name == "toggle_plugin_tool":
            plugin_manager = get_plugin_manager()
            plugin_id = arguments["plugin_id"]
            tool_name = arguments["tool_name"]
            enabled = arguments["enabled"]

            success = await plugin_manager.toggle_tool(plugin_id, tool_name, enabled)
            action = "enabled" if enabled else "disabled"

            if success:
                await state_manager.log("INFO", f"Tool {tool_name} {action} for plugin {plugin_id}")
                return [TextContent(type="text", text=json.dumps({
                    "success": True,
                    "message": f"Tool {action} successfully"
                }, indent=2))]
            else:
                return [TextContent(type="text", text=json.dumps({
                    "success": False,
                    "error": "Tool not found"
                }, indent=2))]

        else:
            return [TextContent(type="text", text=f'{{"error": "Unknown tool: {name}"}}')]
    
    except Exception as e:
        await state_manager.log("ERROR", f"Tool error: {str(e)}")
        return [TextContent(type="text", text=f'{{"error": "{str(e)}"}}')]


async def run_mcp_server():
    """Run the MCP server."""
    init_executor()
    await state_manager.initialize_db()

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    """Main entry point."""
    asyncio.run(run_mcp_server())


if __name__ == "__main__":
    main()
