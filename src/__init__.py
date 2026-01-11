"""Dev Orchestrator MCP - Mac development environment orchestration."""

from .config import get_config, ServerConfig, GuardrailsConfig, ProjectProfile
from .detector import ProjectDetector
from .executor import ShellExecutor, CommandResult, CommandStatus
from .notifications import get_notifier, NotificationHandler
from .state import get_state_manager, StateManager

__version__ = "0.1.0"
__all__ = [
    "get_config",
    "ServerConfig",
    "GuardrailsConfig",
    "ProjectProfile",
    "ProjectDetector",
    "ShellExecutor",
    "CommandResult",
    "CommandStatus",
    "get_notifier",
    "NotificationHandler",
    "get_state_manager",
    "StateManager",
]
