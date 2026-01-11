"""State management and WebSocket broadcasting."""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any
import websockets
from websockets.server import WebSocketServerProtocol

from .config import get_config, ProjectProfile
from .database.engine import get_session_maker, init_db
from .database.repositories import (
    CommandRepository,
    SavedCommandRepository,
    ProjectRepository,
)


@dataclass
class ServiceInfo:
    """Information about a running service."""
    id: str
    name: str
    command: str
    cwd: str
    port: Optional[int]
    pid: int
    started_at: datetime
    status: str = "running"


# Removed AppState dataclass - now using database repositories


class StateManager:
    """Manages application state and broadcasts updates."""

    def __init__(self):
        # WebSocket clients
        self.clients: set[WebSocketServerProtocol] = set()
        self._lock = asyncio.Lock()

        # Ephemeral state (not persisted to database)
        self.current_project: Optional[ProjectProfile] = None
        self.services: dict[str, ServiceInfo] = {}
        self.pending_approvals: list[dict] = []
        self.workspace: Optional[dict] = None

        # Database session and repositories
        self.session_maker = None
        self.command_repo: Optional[CommandRepository] = None
        self.saved_command_repo: Optional[SavedCommandRepository] = None
        self.project_repo: Optional[ProjectRepository] = None
        self._db_initialized = False

    async def initialize_db(self):
        """Initialize database and repositories."""
        if self._db_initialized:
            return

        # Initialize database tables
        await init_db()

        # Create session maker
        self.session_maker = get_session_maker()

        # Create a session for repositories
        # We'll use a long-lived session for the state manager
        session = self.session_maker()
        self.command_repo = CommandRepository(session)
        self.saved_command_repo = SavedCommandRepository(session)
        self.project_repo = ProjectRepository(session)

        self._db_initialized = True
    
    async def broadcast(self, event_type: str, data: Any):
        """Broadcast an event to all connected WebSocket clients."""
        if not self.clients:
            return

        message = json.dumps({
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })

        # Send to all clients, removing disconnected ones
        # Use a copy of the set to avoid RuntimeError during iteration
        disconnected = set()
        for client in list(self.clients):
            try:
                await client.send(message)
            except websockets.ConnectionClosed:
                disconnected.add(client)

        self.clients -= disconnected
    
    async def broadcast_state(self):
        """Broadcast full state to all clients."""
        # Gather state from repositories and in-memory data
        state_dict = await self._get_state_dict()
        await self.broadcast("state", state_dict)

    async def _get_state_dict(self) -> dict:
        """Build state dictionary from repos and in-memory data."""
        # Get recent data from database
        commands = []
        saved_commands = []
        logs = []

        if self.command_repo:
            cmd_list = await self.command_repo.get_recent(50)
            commands = [
                {
                    "id": cmd.id,
                    "command": cmd.command,
                    "cwd": cmd.cwd,
                    "status": cmd.status,
                    "exit_code": cmd.exit_code,
                    "timestamp": cmd.timestamp.isoformat(),
                }
                for cmd in cmd_list
            ]

        if self.saved_command_repo:
            saved_list = await self.saved_command_repo.get_all_with_tags()
            saved_commands = [
                {
                    "id": sc.id,
                    "name": sc.name,
                    "command": sc.command,
                    "cwd": sc.cwd,
                    "description": sc.description,
                    "created_at": sc.created_at.isoformat(),
                    "tags": [tag.name for tag in sc.tags],
                }
                for sc in saved_list
            ]

        # Build state dictionary
        result = {
            "current_project": (
                self.current_project.model_dump(mode="json")
                if self.current_project
                else None
            ),
            "services": {
                k: {
                    "id": v.id,
                    "name": v.name,
                    "command": v.command,
                    "cwd": v.cwd,
                    "port": v.port,
                    "pid": v.pid,
                    "started_at": v.started_at.isoformat(),
                    "status": v.status,
                }
                for k, v in self.services.items()
            },
            "command_history": commands,
            "pending_approvals": self.pending_approvals,
            "logs": logs,  # Will add log repo later
            "saved_commands": saved_commands,
        }

        if self.workspace:
            result["workspace"] = self.workspace

        return result
    
    async def add_client(self, websocket: WebSocketServerProtocol):
        """Add a new WebSocket client."""
        self.clients.add(websocket)
        # Send current state to new client
        state_dict = await self._get_state_dict()
        await websocket.send(
            json.dumps({
                "type": "state",
                "data": state_dict,
                "timestamp": datetime.now().isoformat(),
            })
        )
    
    def remove_client(self, websocket: WebSocketServerProtocol):
        """Remove a WebSocket client."""
        self.clients.discard(websocket)
    
    async def set_project(self, profile: ProjectProfile):
        """Set current project and broadcast update."""
        async with self._lock:
            self.current_project = profile
        await self.broadcast("project_changed", profile.model_dump(mode="json"))

    async def set_workspace(self, workspace_data: dict):
        """Set workspace data and broadcast update."""
        async with self._lock:
            self.workspace = workspace_data
        await self.broadcast("workspace", workspace_data)
    
    async def add_service(self, service: ServiceInfo):
        """Add a running service and broadcast update."""
        async with self._lock:
            self.services[service.id] = service
        await self.broadcast(
            "service_started",
            {
                "id": service.id,
                "name": service.name,
                "port": service.port,
                "pid": service.pid,
            },
        )

    async def remove_service(self, service_id: str):
        """Remove a service and broadcast update."""
        async with self._lock:
            if service_id in self.services:
                del self.services[service_id]
        await self.broadcast("service_stopped", {"id": service_id})

    async def update_service_status(self, service_id: str, status: str):
        """Update service status and broadcast."""
        async with self._lock:
            if service_id in self.services:
                self.services[service_id].status = status
        await self.broadcast("service_status", {"id": service_id, "status": status})
    
    async def add_command(self, command_info: dict):
        """Add command to history and broadcast."""
        if self.command_repo:
            await self.command_repo.add_command(
                command=command_info.get("command", ""),
                cwd=command_info.get("cwd", "."),
                status=command_info.get("status", "unknown"),
                exit_code=command_info.get("exit_code"),
                stdout=command_info.get("stdout"),
                stderr=command_info.get("stderr"),
                project_id=command_info.get("project_id"),
            )
        await self.broadcast("command", command_info)
    
    async def add_pending_approval(self, approval: dict):
        """Add pending approval and broadcast."""
        async with self._lock:
            self.pending_approvals.append(approval)
        await self.broadcast("approval_required", approval)

    async def remove_pending_approval(self, approval_id: str):
        """Remove pending approval and broadcast."""
        async with self._lock:
            self.pending_approvals = [
                a for a in self.pending_approvals if a.get("id") != approval_id
            ]
        await self.broadcast("approval_resolved", {"id": approval_id})
    
    async def log(self, level: str, message: str, source: str = "system"):
        """Add log entry and broadcast."""
        entry = {
            "level": level,
            "message": message,
            "source": source,
            "timestamp": datetime.now().isoformat(),
        }
        # TODO: Add to database when log repository is implemented
        # For now, logs are not persisted
        await self.broadcast("log", entry)

    async def clear_logs(self):
        """Clear all logs and broadcast update."""
        # TODO: Clear from database when log repository is implemented
        await self.broadcast("logs_cleared", {})

    async def add_saved_command(self, command_data: dict):
        """Add a saved command and broadcast update."""
        if self.saved_command_repo:
            await self.saved_command_repo.add_saved_command(
                name=command_data.get("name", ""),
                command=command_data.get("command", ""),
                cwd=command_data.get("cwd"),
                description=command_data.get("description"),
            )
            # Get all saved commands to broadcast
            saved_list = await self.saved_command_repo.get_all_with_tags()
            saved_commands = [
                {
                    "id": sc.id,
                    "name": sc.name,
                    "command": sc.command,
                    "cwd": sc.cwd,
                    "description": sc.description,
                    "created_at": sc.created_at.isoformat(),
                    "tags": [tag.name for tag in sc.tags],
                }
                for sc in saved_list
            ]
            await self.broadcast("saved_commands", saved_commands)

    async def remove_saved_command(self, command_id: str):
        """Remove a saved command and broadcast update."""
        if self.saved_command_repo:
            await self.saved_command_repo.delete_by_id(command_id)
            # Get all saved commands to broadcast
            saved_list = await self.saved_command_repo.get_all_with_tags()
            saved_commands = [
                {
                    "id": sc.id,
                    "name": sc.name,
                    "command": sc.command,
                    "cwd": sc.cwd,
                    "description": sc.description,
                    "created_at": sc.created_at.isoformat(),
                    "tags": [tag.name for tag in sc.tags],
                }
                for sc in saved_list
            ]
            await self.broadcast("saved_commands", saved_commands)


# Singleton instance
_state_manager: Optional[StateManager] = None

def get_state_manager() -> StateManager:
    """Get or create state manager singleton."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager
