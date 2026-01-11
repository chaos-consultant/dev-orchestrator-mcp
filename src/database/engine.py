"""SQLAlchemy async engine configuration."""

import os
from pathlib import Path
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import text

from ..config import get_config

# Global engine instance
_engine: Optional[AsyncEngine] = None
_session_maker: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine() -> AsyncEngine:
    """Get or create the async SQLAlchemy engine."""
    global _engine

    if _engine is None:
        config = get_config()

        # Ensure database directory exists
        config.db_file.parent.mkdir(parents=True, exist_ok=True)

        # Create async engine with SQLite
        database_url = f"sqlite+aiosqlite:///{config.db_file}"

        _engine = create_async_engine(
            database_url,
            echo=False,  # Set to True for SQL logging during development
            poolclass=NullPool,  # SQLite doesn't need pooling
            connect_args={
                "check_same_thread": False,  # Required for async SQLite
            },
        )

    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """Get or create the session maker."""
    global _session_maker

    if _session_maker is None:
        engine = get_engine()
        _session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    return _session_maker


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session (context manager)."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize the database by creating all tables."""
    from .models import Base

    engine = get_engine()

    # Enable WAL mode for better concurrency
    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        await conn.execute(text("PRAGMA synchronous=NORMAL"))

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def close_engine():
    """Close the database engine."""
    global _engine, _session_maker

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_maker = None
