"""Repository for project tracking and sessions."""

from datetime import datetime
from typing import Optional, List
import uuid

from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepository
from ..models import Project, ProjectSession


class ProjectRepository(BaseRepository[Project]):
    """Repository for managing projects and tracking time."""

    def __init__(self, session: AsyncSession):
        """Initialize project repository."""
        super().__init__(session, Project)

    async def get_by_path(self, path: str) -> Optional[Project]:
        """Get a project by its path."""
        result = await self.session.execute(
            select(Project).where(Project.path == path)
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        name: str,
        path: str,
        project_type: Optional[str] = None,
    ) -> Project:
        """Get existing project or create new one."""
        project = await self.get_by_path(path)

        if not project:
            project = Project(
                id=str(uuid.uuid4()),
                name=name,
                path=path,
                project_type=project_type,
                last_accessed=datetime.now(),
                total_time_seconds=0,
            )
            project = await self.add(project)

        return project

    async def start_session(self, project_id: str) -> ProjectSession:
        """
        Start a new session for a project.
        If there's an active session, close it first.
        """
        # Close any active sessions for this project
        await self._close_active_sessions(project_id)

        # Create new session
        session = ProjectSession(
            id=str(uuid.uuid4()),
            project_id=project_id,
            started_at=datetime.now(),
        )
        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)

        # Update project's last_accessed
        project = await self.get_by_id(project_id)
        if project:
            project.last_accessed = datetime.now()
            await self.update(project)

        return session

    async def end_session(self, session_id: str) -> ProjectSession:
        """End an active project session."""
        result = await self.session.execute(
            select(ProjectSession).where(ProjectSession.id == session_id)
        )
        project_session = result.scalar_one_or_none()

        if not project_session:
            raise ValueError(f"Session {session_id} not found")

        if project_session.ended_at:
            return project_session  # Already ended

        # Calculate duration
        project_session.ended_at = datetime.now()
        duration = (project_session.ended_at - project_session.started_at).total_seconds()
        project_session.duration_seconds = int(duration)

        # Update project's total time
        project = await self.get_by_id(project_session.project_id)
        if project:
            project.total_time_seconds += int(duration)
            await self.update(project)

        await self.session.commit()
        await self.session.refresh(project_session)

        return project_session

    async def get_active_session(self, project_id: str) -> Optional[ProjectSession]:
        """Get the currently active session for a project."""
        result = await self.session.execute(
            select(ProjectSession)
            .where(ProjectSession.project_id == project_id)
            .where(ProjectSession.ended_at.is_(None))
            .order_by(desc(ProjectSession.started_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_time_spent(self, project_id: str) -> int:
        """Get total time spent on a project in seconds."""
        project = await self.get_by_id(project_id)
        return project.total_time_seconds if project else 0

    async def get_session_history(
        self, project_id: str, limit: int = 50
    ) -> List[ProjectSession]:
        """Get recent sessions for a project."""
        result = await self.session.execute(
            select(ProjectSession)
            .where(ProjectSession.project_id == project_id)
            .order_by(desc(ProjectSession.started_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recently_accessed(self, limit: int = 10) -> List[Project]:
        """Get recently accessed projects."""
        result = await self.session.execute(
            select(Project)
            .where(Project.last_accessed.is_not(None))
            .order_by(desc(Project.last_accessed))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_most_used(self, limit: int = 10) -> List[Project]:
        """Get projects with most time spent."""
        result = await self.session.execute(
            select(Project)
            .order_by(desc(Project.total_time_seconds))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def _close_active_sessions(self, project_id: str) -> None:
        """Close all active sessions for a project."""
        result = await self.session.execute(
            select(ProjectSession)
            .where(ProjectSession.project_id == project_id)
            .where(ProjectSession.ended_at.is_(None))
        )
        active_sessions = result.scalars().all()

        for session in active_sessions:
            session.ended_at = datetime.now()
            duration = (session.ended_at - session.started_at).total_seconds()
            session.duration_seconds = int(duration)

            # Update project total
            project = await self.get_by_id(project_id)
            if project:
                project.total_time_seconds += int(duration)

        await self.session.commit()
