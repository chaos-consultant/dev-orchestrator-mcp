"""Base repository with common CRUD operations."""

from typing import Generic, Type, TypeVar, Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository providing common database operations."""

    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        """Initialize repository with session and model type."""
        self.session = session
        self.model = model

    async def get_by_id(self, id: str) -> Optional[ModelType]:
        """Get a single record by ID."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, limit: Optional[int] = None) -> List[ModelType]:
        """Get all records, optionally limited."""
        query = select(self.model)
        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def add(self, instance: ModelType) -> ModelType:
        """Add a new record."""
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def update(self, instance: ModelType) -> ModelType:
        """Update an existing record."""
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def delete(self, instance: ModelType) -> None:
        """Delete a record."""
        await self.session.delete(instance)
        await self.session.commit()

    async def delete_by_id(self, id: str) -> bool:
        """Delete a record by ID. Returns True if deleted, False if not found."""
        instance = await self.get_by_id(id)
        if instance:
            await self.delete(instance)
            return True
        return False
