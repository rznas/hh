"""Database connection and session management."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..config.settings import get_settings
from ..models.base import Base


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self) -> None:
        """Initialize database manager."""
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    def initialize(self, database_url: str | None = None) -> None:
        """Initialize database engine and session factory.

        Args:
            database_url: Optional database URL override
        """
        settings = get_settings()
        url = database_url or settings.database_url

        self._engine = create_async_engine(
            url,
            echo=settings.database_echo,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_pre_ping=True,
        )

        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @property
    def engine(self) -> AsyncEngine:
        """Get database engine."""
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get session factory."""
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._session_factory

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Create a new database session.

        Yields:
            AsyncSession: Database session

        Example:
            async with db_manager.session() as session:
                result = await session.execute(query)
        """
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def create_tables(self) -> None:
        """Create all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        """Drop all database tables. USE WITH CAUTION!"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def close(self) -> None:
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()


# Global database manager instance
db_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session.

    Yields:
        AsyncSession: Database session

    Example:
        async with get_db_session() as session:
            result = await session.execute(query)
    """
    async with db_manager.session() as session:
        yield session
