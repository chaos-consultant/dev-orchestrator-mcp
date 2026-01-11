"""Repository for command history operations."""

from datetime import datetime
from typing import Optional, List, Tuple
import uuid

from sqlalchemy import select, desc, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from .base import BaseRepository
from ..models import Command


class CommandRepository(BaseRepository[Command]):
    """Repository for managing command history."""

    def __init__(self, session: AsyncSession):
        """Initialize command repository."""
        super().__init__(session, Command)

    async def get_recent(self, limit: int = 50) -> List[Command]:
        """Get most recent commands."""
        result = await self.session.execute(
            select(Command)
            .order_by(desc(Command.timestamp))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search(
        self,
        text_query: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Command]:
        """
        Search commands with filters.

        Args:
            text_query: Full-text search query (searches command, stdout, stderr)
            start_date: Filter commands after this date
            end_date: Filter commands before this date
            status: Filter by status
            project_id: Filter by project
            limit: Maximum results to return
        """
        query = select(Command)

        # Apply filters
        conditions = []

        if text_query:
            # Full-text search using FTS5
            # Note: FTS5 implementation would require virtual table setup
            # For now, use LIKE for basic search
            search_pattern = f"%{text_query}%"
            conditions.append(
                or_(
                    Command.command.like(search_pattern),
                    Command.stdout.like(search_pattern),
                    Command.stderr.like(search_pattern),
                )
            )

        if start_date:
            conditions.append(Command.timestamp >= start_date)

        if end_date:
            conditions.append(Command.timestamp <= end_date)

        if status:
            conditions.append(Command.status == status)

        if project_id:
            conditions.append(Command.project_id == project_id)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(desc(Command.timestamp)).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def add_command(
        self,
        command: str,
        cwd: str,
        status: str,
        exit_code: Optional[int] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Command:
        """Add a new command to history."""
        cmd = Command(
            id=str(uuid.uuid4()),
            command=command,
            cwd=cwd,
            status=status,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            timestamp=datetime.now(),
            project_id=project_id,
        )
        return await self.add(cmd)

    async def get_by_project(
        self, project_id: str, limit: int = 50
    ) -> List[Command]:
        """Get commands for a specific project."""
        result = await self.session.execute(
            select(Command)
            .where(Command.project_id == project_id)
            .order_by(desc(Command.timestamp))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_failed_commands(self, limit: int = 50) -> List[Command]:
        """Get recent failed commands (exit_code != 0)."""
        result = await self.session.execute(
            select(Command)
            .where(Command.exit_code != 0)
            .where(Command.exit_code.is_not(None))
            .order_by(desc(Command.timestamp))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_total(self) -> int:
        """Get total number of commands in history."""
        result = await self.session.execute(
            select(func.count()).select_from(Command)
        )
        return result.scalar_one()

    async def cleanup_old(self, keep_last: int = 10000) -> int:
        """
        Delete old commands, keeping only the most recent ones.
        Returns number of deleted commands.
        """
        # Get the timestamp of the Nth most recent command
        subquery = (
            select(Command.timestamp)
            .order_by(desc(Command.timestamp))
            .offset(keep_last)
            .limit(1)
        )
        result = await self.session.execute(subquery)
        cutoff_time = result.scalar_one_or_none()

        if cutoff_time is None:
            return 0  # Less than keep_last commands exist

        # Delete commands older than cutoff
        delete_query = text(
            "DELETE FROM commands WHERE timestamp < :cutoff_time"
        )
        result = await self.session.execute(
            delete_query, {"cutoff_time": cutoff_time}
        )
        await self.session.commit()

        return result.rowcount or 0
