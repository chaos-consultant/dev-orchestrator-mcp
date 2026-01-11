"""Plugin manager for MCP servers."""

from pathlib import Path
from typing import Optional, List
from datetime import datetime

from ..config import get_config
from ..database.repositories import PluginRepository
from ..database.engine import get_session_maker
from .installer import PluginInstaller
from .models import PluginInfo, PluginToolInfo, InstallResult, PluginManifest


class PluginManager:
    """Manages MCP server plugins."""

    def __init__(self):
        """Initialize plugin manager."""
        config = get_config()
        self.plugins_dir = Path("~/.dev-orchestrator/plugins").expanduser()
        self.plugins_dir.mkdir(parents=True, exist_ok=True)

        self.installer = PluginInstaller(self.plugins_dir)
        self.session_maker = get_session_maker()

    async def list_installed(self) -> List[PluginInfo]:
        """
        List all installed plugins.

        Returns:
            List of PluginInfo objects
        """
        async with self.session_maker() as session:
            repo = PluginRepository(session)
            plugins = await repo.get_all_with_tools()

            return [
                PluginInfo(
                    id=p.id,
                    name=p.name,
                    git_url=p.git_url,
                    version=p.version,
                    author=p.author,
                    description=p.description,
                    installed_at=p.installed_at,
                    enabled=p.enabled,
                    install_path=p.install_path,
                    tools=[
                        PluginToolInfo(
                            id=t.id,
                            plugin_id=t.plugin_id,
                            tool_name=t.tool_name,
                            enabled=t.enabled,
                        )
                        for t in p.tools
                    ],
                )
                for p in plugins
            ]

    async def install(self, git_url: str) -> InstallResult:
        """
        Install a plugin from a git repository.

        Args:
            git_url: Git repository URL

        Returns:
            InstallResult with status and details
        """
        # Install plugin files
        success, message, install_path = await self.installer.install_from_git(git_url)

        if not success or not install_path:
            return InstallResult(
                success=False,
                message=message,
                error="Installation failed",
            )

        try:
            # Read manifest to get metadata
            manifest = await self.installer._read_manifest(install_path)
            if not manifest:
                # Cleanup
                await self.installer.uninstall(install_path)
                return InstallResult(
                    success=False,
                    message="Could not read plugin manifest",
                    error="Missing or invalid manifest file",
                )

            # Check if plugin already exists in database
            async with self.session_maker() as session:
                repo = PluginRepository(session)
                existing = await repo.get_by_name(manifest.name)

                if existing:
                    # Cleanup files
                    await self.installer.uninstall(install_path)
                    return InstallResult(
                        success=False,
                        message=f"Plugin {manifest.name} is already installed",
                        error="Duplicate plugin",
                    )

                # Add to database
                plugin = await repo.add_plugin(
                    name=manifest.name,
                    git_url=git_url,
                    install_path=str(install_path),
                    version=manifest.version,
                    author=manifest.author,
                    description=manifest.description,
                    tool_names=manifest.tools,
                )

                return InstallResult(
                    success=True,
                    plugin_id=plugin.id,
                    message=f"Successfully installed {manifest.name}",
                )

        except Exception as e:
            # Cleanup on error
            if install_path:
                await self.installer.uninstall(install_path)

            return InstallResult(
                success=False,
                message=f"Installation failed: {str(e)}",
                error=str(e),
            )

    async def uninstall(self, plugin_id: str) -> InstallResult:
        """
        Uninstall a plugin.

        Args:
            plugin_id: Plugin ID

        Returns:
            InstallResult with status
        """
        async with self.session_maker() as session:
            repo = PluginRepository(session)
            plugin = await repo.get_by_id(plugin_id)

            if not plugin:
                return InstallResult(
                    success=False,
                    message="Plugin not found",
                    error="Invalid plugin ID",
                )

            # Remove files
            install_path = Path(plugin.install_path)
            file_success, file_message = await self.installer.uninstall(install_path)

            # Remove from database
            db_success = await repo.delete_plugin(plugin_id)

            if file_success and db_success:
                return InstallResult(
                    success=True,
                    message=f"Successfully uninstalled {plugin.name}",
                )
            else:
                return InstallResult(
                    success=False,
                    message=f"Partial uninstall: {file_message}",
                    error="Could not completely remove plugin",
                )

    async def toggle(self, plugin_id: str, enabled: bool) -> bool:
        """
        Enable or disable a plugin.

        Args:
            plugin_id: Plugin ID
            enabled: True to enable, False to disable

        Returns:
            True if successful, False otherwise
        """
        async with self.session_maker() as session:
            repo = PluginRepository(session)
            plugin = await repo.toggle_plugin(plugin_id, enabled)
            return plugin is not None

    async def toggle_tool(
        self, plugin_id: str, tool_name: str, enabled: bool
    ) -> bool:
        """
        Enable or disable a specific tool.

        Args:
            plugin_id: Plugin ID
            tool_name: Tool name
            enabled: True to enable, False to disable

        Returns:
            True if successful, False otherwise
        """
        async with self.session_maker() as session:
            repo = PluginRepository(session)
            tool = await repo.toggle_tool(plugin_id, tool_name, enabled)
            return tool is not None

    async def get_enabled_tools(self) -> dict[str, str]:
        """
        Get all enabled tools from enabled plugins.

        Returns:
            Dictionary mapping tool names to plugin IDs
        """
        async with self.session_maker() as session:
            repo = PluginRepository(session)
            plugins = await repo.get_enabled_plugins()

            tools = {}
            for plugin in plugins:
                for tool in plugin.tools:
                    if tool.enabled:
                        tools[tool.tool_name] = plugin.id

            return tools


# Singleton instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get or create plugin manager singleton."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager
