"""Configuration and guardrails for dev-orchestrator-mcp."""

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional
import json


class GuardrailsConfig(BaseModel):
    """Security guardrails for shell command execution."""
    
    # Commands that are always blocked - no approval possible
    blocked_commands: list[str] = Field(default=[
        "rm -rf /",
        "rm -rf ~",
        "rm -rf $HOME",
        "rm -rf /*",
        "rm -rf ~/*",
        "sudo rm -rf",
        "mkfs",
        "dd if=",
        "> /dev/sda",
        "chmod -R 777 /",
        ":(){ :|:& };:",  # fork bomb
    ])
    
    # Patterns that require interactive approval
    approval_required_patterns: list[str] = Field(default=[
        "rm -rf",
        "rm -r",
        "git push --force",
        "git push -f",
        "git reset --hard",
        "git clean -fd",
        "DROP TABLE",
        "DROP DATABASE",
        "DELETE FROM",
        "TRUNCATE",
        "sudo ",
        "chmod -R",
        "chown -R",
        "kill -9",
        "killall",
        "pkill",
        "shutdown",
        "reboot",
        "npm publish",
        "pip upload",
        "twine upload",
    ])
    
    # Allowed base directories for operations
    allowed_directories: list[str] = Field(default=[
        "~/work",
        "~/personal",
        "~/repos",
        "~/projects",
        "~/dev",
    ])
    
    # Git remotes that require approval for push
    protected_git_remotes: list[str] = Field(default=[
        "origin",
        "upstream",
    ])

    def is_blocked(self, command: str) -> bool:
        """Check if command is in absolute blocklist."""
        cmd_lower = command.lower().strip()
        for blocked in self.blocked_commands:
            if blocked.lower() in cmd_lower:
                return True
        return False
    
    def requires_approval(self, command: str) -> tuple[bool, Optional[str]]:
        """Check if command requires interactive approval. Returns (needs_approval, reason)."""
        cmd_lower = command.lower().strip()
        for pattern in self.approval_required_patterns:
            if pattern.lower() in cmd_lower:
                return True, f"Command contains '{pattern}' which requires approval"
        return False, None
    
    def is_in_allowed_directory(self, path: str) -> bool:
        """Check if path is within allowed directories."""
        expanded_path = Path(path).expanduser().resolve()
        for allowed in self.allowed_directories:
            allowed_path = Path(allowed).expanduser().resolve()
            try:
                expanded_path.relative_to(allowed_path)
                return True
            except ValueError:
                continue
        return False


class ProjectProfile(BaseModel):
    """Detected project configuration."""
    
    path: Path
    name: str
    project_type: list[str] = Field(default_factory=list)  # e.g., ["python", "fastapi", "react"]
    
    # Python specifics
    has_python: bool = False
    python_version: Optional[str] = None
    venv_path: Optional[Path] = None
    has_fastapi: bool = False
    has_pytest: bool = False
    
    # Node specifics
    has_node: bool = False
    node_version: Optional[str] = None
    has_react: bool = False
    has_vite: bool = False
    package_manager: Optional[str] = None  # npm, yarn, pnpm
    
    # Git specifics
    has_git: bool = False
    git_remote: Optional[str] = None
    git_branch: Optional[str] = None
    git_user_email: Optional[str] = None
    git_user_name: Optional[str] = None
    
    # Common ports
    backend_port: Optional[int] = None
    frontend_port: Optional[int] = None


class ServerConfig(BaseSettings):
    """Main server configuration."""
    
    host: str = "127.0.0.1"
    mcp_port: int = 8765
    dashboard_port: int = 3333
    websocket_port: int = 8766
    
    log_level: str = "INFO"
    log_file: Path = Path("~/.dev-orchestrator/logs/server.log").expanduser()
    
    state_file: Path = Path("~/.dev-orchestrator/state.json").expanduser()
    config_file: Path = Path("~/.dev-orchestrator/config.json").expanduser()
    
    guardrails: GuardrailsConfig = Field(default_factory=GuardrailsConfig)
    
    class Config:
        env_prefix = "DEV_ORCH_"
    
    def save(self):
        """Save configuration to file."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.model_dump(mode='json'), f, indent=2, default=str)
    
    @classmethod
    def load(cls) -> "ServerConfig":
        """Load configuration from file or create default."""
        config_path = Path("~/.dev-orchestrator/config.json").expanduser()
        if config_path.exists():
            with open(config_path) as f:
                data = json.load(f)
                return cls(**data)
        return cls()


# Singleton instance
_config: Optional[ServerConfig] = None

def get_config() -> ServerConfig:
    """Get or create configuration singleton."""
    global _config
    if _config is None:
        _config = ServerConfig.load()
    return _config
