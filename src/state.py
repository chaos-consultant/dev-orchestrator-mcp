"""State management and WebSocket broadcasting."""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Any
import websockets
from websockets.server import WebSocketServerProtocol

from .config import get_config, ProjectProfile


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


@dataclass
class AppState:
    """Global application state."""
    current_project: Optional[ProjectProfile] = None
    services: dict[str, ServiceInfo] = field(default_factory=dict)
    command_history: list[dict] = field(default_factory=list)
    pending_approvals: list[dict] = field(default_factory=list)
    logs: list[dict] = field(default_factory=list)
    workspace: Optional[dict] = None

    def to_dict(self) -> dict:
        """Convert state to dictionary for JSON serialization."""
        result = {
            "current_project": self.current_project.model_dump(mode='json') if self.current_project else None,
            "services": {
                k: {
                    "id": v.id,
                    "name": v.name,
                    "command": v.command,
                    "cwd": v.cwd,
                    "port": v.port,
                    "pid": v.pid,
                    "started_at": v.started_at.isoformat(),
                    "status": v.status
                }
                for k, v in self.services.items()
            },
            "command_history": self.command_history[-50:],
            "pending_approvals": self.pending_approvals,
            "logs": self.logs[-100:],
        }
        if self.workspace:
            result["workspace"] = self.workspace
        return result


class StateManager:
    """Manages application state and broadcasts updates."""
    
    def __init__(self):
        self.state = AppState()
        self.clients: set[WebSocketServerProtocol] = set()
        self._log_buffer: list[dict] = []
        self._lock = asyncio.Lock()
    
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
        await self.broadcast("state", self.state.to_dict())
    
    async def add_client(self, websocket: WebSocketServerProtocol):
        """Add a new WebSocket client."""
        self.clients.add(websocket)
        # Send current state to new client
        await websocket.send(json.dumps({
            "type": "state",
            "data": self.state.to_dict(),
            "timestamp": datetime.now().isoformat()
        }))
    
    def remove_client(self, websocket: WebSocketServerProtocol):
        """Remove a WebSocket client."""
        self.clients.discard(websocket)
    
    async def set_project(self, profile: ProjectProfile):
        """Set current project and broadcast update."""
        async with self._lock:
            self.state.current_project = profile
        await self.broadcast("project_changed", profile.model_dump(mode='json'))

    async def set_workspace(self, workspace_data: dict):
        """Set workspace data and broadcast update."""
        async with self._lock:
            self.state.workspace = workspace_data
        await self.broadcast("workspace", workspace_data)
    
    async def add_service(self, service: ServiceInfo):
        """Add a running service and broadcast update."""
        async with self._lock:
            self.state.services[service.id] = service
        await self.broadcast("service_started", {
            "id": service.id,
            "name": service.name,
            "port": service.port,
            "pid": service.pid
        })
    
    async def remove_service(self, service_id: str):
        """Remove a service and broadcast update."""
        async with self._lock:
            if service_id in self.state.services:
                del self.state.services[service_id]
        await self.broadcast("service_stopped", {"id": service_id})
    
    async def update_service_status(self, service_id: str, status: str):
        """Update service status and broadcast."""
        async with self._lock:
            if service_id in self.state.services:
                self.state.services[service_id].status = status
        await self.broadcast("service_status", {"id": service_id, "status": status})
    
    async def add_command(self, command_info: dict):
        """Add command to history and broadcast."""
        async with self._lock:
            self.state.command_history.append(command_info)
            if len(self.state.command_history) > 100:
                self.state.command_history = self.state.command_history[-100:]
        await self.broadcast("command", command_info)
    
    async def add_pending_approval(self, approval: dict):
        """Add pending approval and broadcast."""
        async with self._lock:
            self.state.pending_approvals.append(approval)
        await self.broadcast("approval_required", approval)
    
    async def remove_pending_approval(self, approval_id: str):
        """Remove pending approval and broadcast."""
        async with self._lock:
            self.state.pending_approvals = [
                a for a in self.state.pending_approvals
                if a.get("id") != approval_id
            ]
        await self.broadcast("approval_resolved", {"id": approval_id})
    
    async def log(self, level: str, message: str, source: str = "system"):
        """Add log entry and broadcast."""
        entry = {
            "level": level,
            "message": message,
            "source": source,
            "timestamp": datetime.now().isoformat()
        }
        async with self._lock:
            self.state.logs.append(entry)
            if len(self.state.logs) > 500:
                self.state.logs = self.state.logs[-500:]
        await self.broadcast("log", entry)
    
    def save_state(self):
        """Save state to disk."""
        config = get_config()
        config.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config.state_file, 'w') as f:
            json.dump(self.state.to_dict(), f, indent=2)
    
    def load_state(self):
        """Load state from disk."""
        config = get_config()
        if config.state_file.exists():
            try:
                with open(config.state_file) as f:
                    data = json.load(f)
                    self.state.command_history = data.get("command_history", [])
                    self.state.logs = data.get("logs", [])
            except Exception:
                pass


# Singleton instance
_state_manager: Optional[StateManager] = None

def get_state_manager() -> StateManager:
    """Get or create state manager singleton."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager
