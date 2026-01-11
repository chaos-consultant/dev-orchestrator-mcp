"""Repository for saved commands and tags."""

from datetime import datetime
from typing import Optional, List
import uuid

from sqlalchemy import select, desc, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepository
from ..models import SavedCommand, Tag, CommandTag


class SavedCommandRepository(BaseRepository[SavedCommand]):
    """Repository for managing saved/favorite commands."""

    def __init__(self, session: AsyncSession):
        """Initialize saved command repository."""
        super().__init__(session, SavedCommand)

    async def get_all_with_tags(self) -> List[SavedCommand]:
        """Get all saved commands with their tags loaded."""
        result = await self.session.execute(
            select(SavedCommand).options(selectinload(SavedCommand.tags))
        )
        return list(result.scalars().all())

    async def get_with_tags(self, command_id: str) -> Optional[SavedCommand]:
        """Get a saved command with tags loaded."""
        result = await self.session.execute(
            select(SavedCommand)
            .where(SavedCommand.id == command_id)
            .options(selectinload(SavedCommand.tags))
        )
        return result.scalar_one_or_none()

    async def add_saved_command(
        self,
        name: str,
        command: str,
        cwd: Optional[str] = None,
        description: Optional[str] = None,
        tag_names: Optional[List[str]] = None,
    ) -> SavedCommand:
        """
        Add a new saved command with optional tags.

        Args:
            name: Display name for the command
            command: The actual command string
            cwd: Working directory
            description: Optional description
            tag_names: List of tag names to apply
        """
        saved_cmd = SavedCommand(
            id=str(uuid.uuid4()),
            name=name,
            command=command,
            cwd=cwd,
            description=description,
            created_at=datetime.now(),
        )

        self.session.add(saved_cmd)

        # Add tags if provided
        if tag_names:
            tags = await self._get_or_create_tags(tag_names)
            saved_cmd.tags.extend(tags)

        await self.session.commit()
        await self.session.refresh(saved_cmd, ["tags"])

        return saved_cmd

    async def update_last_used(self, command_id: str) -> None:
        """Update the last_used timestamp for a command."""
        saved_cmd = await self.get_by_id(command_id)
        if saved_cmd:
            saved_cmd.last_used = datetime.now()
            await self.update(saved_cmd)

    async def search_by_name(self, query: str) -> List[SavedCommand]:
        """Search saved commands by name."""
        result = await self.session.execute(
            select(SavedCommand)
            .where(SavedCommand.name.like(f"%{query}%"))
            .options(selectinload(SavedCommand.tags))
        )
        return list(result.scalars().all())

    async def search_by_tag(self, tag_name: str) -> List[SavedCommand]:
        """Get all saved commands with a specific tag."""
        result = await self.session.execute(
            select(SavedCommand)
            .join(SavedCommand.tags)
            .where(Tag.name == tag_name)
            .options(selectinload(SavedCommand.tags))
        )
        return list(result.scalars().all())

    async def add_tag_to_command(
        self, command_id: str, tag_name: str
    ) -> SavedCommand:
        """Add a tag to a saved command."""
        saved_cmd = await self.get_by_id(command_id)
        if not saved_cmd:
            raise ValueError(f"Command {command_id} not found")

        tag = await self._get_or_create_tag(tag_name)

        if tag not in saved_cmd.tags:
            saved_cmd.tags.append(tag)
            await self.session.commit()

        await self.session.refresh(saved_cmd, ["tags"])
        return saved_cmd

    async def remove_tag_from_command(
        self, command_id: str, tag_name: str
    ) -> SavedCommand:
        """Remove a tag from a saved command."""
        saved_cmd = await self.get_by_id(command_id)
        if not saved_cmd:
            raise ValueError(f"Command {command_id} not found")

        # Load tags
        await self.session.refresh(saved_cmd, ["tags"])

        # Find and remove tag
        tag_to_remove = None
        for tag in saved_cmd.tags:
            if tag.name == tag_name:
                tag_to_remove = tag
                break

        if tag_to_remove:
            saved_cmd.tags.remove(tag_to_remove)
            await self.session.commit()

        return saved_cmd

    async def get_all_tags(self) -> List[Tag]:
        """Get all available tags."""
        result = await self.session.execute(select(Tag))
        return list(result.scalars().all())

    async def _get_or_create_tag(self, tag_name: str, color: Optional[str] = None) -> Tag:
        """Get existing tag or create new one."""
        result = await self.session.execute(
            select(Tag).where(Tag.name == tag_name)
        )
        tag = result.scalar_one_or_none()

        if not tag:
            tag = Tag(
                id=str(uuid.uuid4()),
                name=tag_name,
                color=color,
                created_at=datetime.now(),
            )
            self.session.add(tag)

        return tag

    async def _get_or_create_tags(self, tag_names: List[str]) -> List[Tag]:
        """Get or create multiple tags."""
        tags = []
        for tag_name in tag_names:
            tag = await self._get_or_create_tag(tag_name)
            tags.append(tag)
        return tags

    async def delete_tag(self, tag_name: str) -> bool:
        """Delete a tag (will be removed from all commands)."""
        result = await self.session.execute(
            select(Tag).where(Tag.name == tag_name)
        )
        tag = result.scalar_one_or_none()

        if tag:
            await self.session.delete(tag)
            await self.session.commit()
            return True

        return False
