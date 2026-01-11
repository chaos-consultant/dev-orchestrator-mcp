"""Repository for plugin management."""

from datetime import datetime
from typing import Optional, List
import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepository
from ..models import Plugin, PluginTool


class PluginRepository(BaseRepository[Plugin]):
    """Repository for managing installed plugins."""

    def __init__(self, session: AsyncSession):
        """Initialize plugin repository."""
        super().__init__(session, Plugin)

    async def get_all_with_tools(self) -> List[Plugin]:
        """Get all plugins with their tools loaded."""
        result = await self.session.execute(
            select(Plugin).options(selectinload(Plugin.tools))
        )
        return list(result.scalars().all())

    async def get_with_tools(self, plugin_id: str) -> Optional[Plugin]:
        """Get a plugin with tools loaded."""
        result = await self.session.execute(
            select(Plugin)
            .where(Plugin.id == plugin_id)
            .options(selectinload(Plugin.tools))
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Plugin]:
        """Get a plugin by its name."""
        result = await self.session.execute(
            select(Plugin).where(Plugin.name == name)
        )
        return result.scalar_one_or_none()

    async def add_plugin(
        self,
        name: str,
        git_url: str,
        install_path: str,
        version: Optional[str] = None,
        author: Optional[str] = None,
        description: Optional[str] = None,
        tool_names: Optional[List[str]] = None,
    ) -> Plugin:
        """
        Add a new plugin with optional tools.

        Args:
            name: Plugin name
            git_url: Git repository URL
            install_path: Local installation path
            version: Plugin version
            author: Plugin author
            description: Plugin description
            tool_names: List of tool names provided by the plugin

        Returns:
            Created Plugin instance
        """
        plugin = Plugin(
            id=str(uuid.uuid4()),
            name=name,
            git_url=git_url,
            version=version,
            author=author,
            description=description,
            installed_at=datetime.now(),
            enabled=True,
            install_path=install_path,
        )

        self.session.add(plugin)

        # Add tools if provided
        if tool_names:
            for tool_name in tool_names:
                tool = PluginTool(
                    id=str(uuid.uuid4()),
                    plugin_id=plugin.id,
                    tool_name=tool_name,
                    enabled=True,
                )
                self.session.add(tool)

        await self.session.commit()
        await self.session.refresh(plugin, ["tools"])

        return plugin

    async def toggle_plugin(self, plugin_id: str, enabled: bool) -> Optional[Plugin]:
        """Enable or disable a plugin and all its tools."""
        plugin = await self.get_with_tools(plugin_id)
        if not plugin:
            return None

        plugin.enabled = enabled
        # Also toggle all tools
        for tool in plugin.tools:
            tool.enabled = enabled

        await self.update(plugin)
        return plugin

    async def toggle_tool(
        self, plugin_id: str, tool_name: str, enabled: bool
    ) -> Optional[PluginTool]:
        """Enable or disable a specific tool."""
        result = await self.session.execute(
            select(PluginTool)
            .where(PluginTool.plugin_id == plugin_id)
            .where(PluginTool.tool_name == tool_name)
        )
        tool = result.scalar_one_or_none()

        if tool:
            tool.enabled = enabled
            await self.session.commit()

        return tool

    async def get_enabled_plugins(self) -> List[Plugin]:
        """Get all enabled plugins with their tools."""
        result = await self.session.execute(
            select(Plugin)
            .where(Plugin.enabled == True)
            .options(selectinload(Plugin.tools))
        )
        return list(result.scalars().all())

    async def delete_plugin(self, plugin_id: str) -> bool:
        """Delete a plugin and all its tools (cascade)."""
        plugin = await self.get_by_id(plugin_id)
        if not plugin:
            return False

        await self.session.delete(plugin)
        await self.session.commit()
        return True
