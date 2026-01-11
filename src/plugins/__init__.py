"""Plugin management package."""

from .manager import PluginManager, get_plugin_manager
from .models import PluginInfo, PluginToolInfo, InstallResult, PluginManifest
from .installer import PluginInstaller

__all__ = [
    "PluginManager",
    "get_plugin_manager",
    "PluginInfo",
    "PluginToolInfo",
    "InstallResult",
    "PluginManifest",
    "PluginInstaller",
]
