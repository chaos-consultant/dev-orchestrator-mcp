"""macOS notification handler."""

import subprocess
import asyncio
from typing import Optional
from enum import Enum


class NotificationType(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    APPROVAL = "approval"


class NotificationHandler:
    """Handles macOS notifications via osascript."""
    
    def __init__(self, app_name: str = "Dev Orchestrator"):
        self.app_name = app_name
        self._enabled = True
    
    def enable(self):
        """Enable notifications."""
        self._enabled = True
    
    def disable(self):
        """Disable notifications."""
        self._enabled = False
    
    async def send(
        self,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        sound: bool = True
    ) -> bool:
        """Send a macOS notification."""
        if not self._enabled:
            return False
        
        # Build osascript command
        sound_str = 'sound name "Ping"' if sound else ""
        
        # Escape quotes in message and title
        title = title.replace('"', '\\"')
        message = message.replace('"', '\\"')
        
        script = f'''
        display notification "{message}" with title "{self.app_name}" subtitle "{title}" {sound_str}
        '''
        
        try:
            proc = await asyncio.create_subprocess_exec(
                "osascript", "-e", script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            return proc.returncode == 0
        except Exception:
            return False
    
    async def notify_command_started(self, command: str, cwd: str):
        """Notify when a command starts."""
        await self.send(
            "Command Started",
            f"Running: {command[:50]}...",
            NotificationType.INFO,
            sound=False
        )
    
    async def notify_command_completed(self, command: str, success: bool):
        """Notify when a command completes."""
        if success:
            await self.send(
                "Command Completed",
                f"Success: {command[:50]}...",
                NotificationType.SUCCESS
            )
        else:
            await self.send(
                "Command Failed",
                f"Failed: {command[:50]}...",
                NotificationType.ERROR
            )
    
    async def notify_approval_required(self, command: str, reason: str):
        """Notify when a command requires approval."""
        await self.send(
            "⚠️ Approval Required",
            f"{command[:40]}... - {reason}",
            NotificationType.APPROVAL
        )
    
    async def notify_service_started(self, service_name: str, port: int):
        """Notify when a service starts."""
        await self.send(
            "Service Started",
            f"{service_name} running on port {port}",
            NotificationType.SUCCESS
        )
    
    async def notify_service_stopped(self, service_name: str):
        """Notify when a service stops."""
        await self.send(
            "Service Stopped",
            service_name,
            NotificationType.INFO
        )
    
    async def notify_error(self, title: str, message: str):
        """Send an error notification."""
        await self.send(title, message, NotificationType.ERROR)
    
    async def notify_project_detected(self, project_name: str, project_types: list[str]):
        """Notify when a project is detected."""
        types_str = ", ".join(project_types)
        await self.send(
            "Project Detected",
            f"{project_name}: {types_str}",
            NotificationType.INFO,
            sound=False
        )


# Singleton instance
_notifier: Optional[NotificationHandler] = None

def get_notifier() -> NotificationHandler:
    """Get or create notification handler singleton."""
    global _notifier
    if _notifier is None:
        _notifier = NotificationHandler()
    return _notifier
