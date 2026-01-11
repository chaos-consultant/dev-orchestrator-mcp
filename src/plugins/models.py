"""Plugin metadata models."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PluginManifest(BaseModel):
    """Plugin manifest from mcp_server.json or package.json."""

    name: str
    version: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    tools: List[str] = Field(default_factory=list)
    entry_point: Optional[str] = None  # Main script/executable
    dependencies: dict[str, list[str]] = Field(default_factory=dict)  # e.g., {"npm": ["typescript"], "pip": ["requests"]}


class PluginInfo(BaseModel):
    """Complete plugin information including database and manifest data."""

    id: str
    name: str
    git_url: str
    version: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    installed_at: datetime
    enabled: bool
    install_path: str
    tools: List["PluginToolInfo"] = Field(default_factory=list)


class PluginToolInfo(BaseModel):
    """Information about a tool provided by a plugin."""

    id: str
    plugin_id: str
    tool_name: str
    enabled: bool


class InstallResult(BaseModel):
    """Result of plugin installation."""

    success: bool
    plugin_id: Optional[str] = None
    message: str
    error: Optional[str] = None
