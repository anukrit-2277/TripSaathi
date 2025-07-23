"""
TripSaathi Database Configuration
====================================
Sets up SQLAlchemy async engine, session factory, and connection management.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    pass


def _get_database_url() -> str:
    """
    Fix the DATABASE_URL for async usage.
    Railway gives: postgresql://user:pass@host:port/db
    We need:      postgresql+asyncpg://user:pass@host:port/db
    """
    url = settings.database_url
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


# Lazy initialization — engine and session are created on first use,
# not at import time. This prevents crashes if DATABASE_URL is invalid.
_engine = None
_async_session = None


def _get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            _get_database_url(),
            pool_size=5,
            max_overflow=10,
            echo=False,
        )
    return _engine


def _get_session_factory():
    global _async_session
    if _async_session is None:
        _async_session = async_sessionmaker(
            _get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session


async def get_db() -> AsyncSession:
    """Dependency injection for FastAPI routes."""
    session_factory = _get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Create all database tables. Called once during app startup."""
    engine = _get_engine()
    async with engine.begin() as conn:
        from app.db import models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def close_db():
    """Close the database engine and all connections."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
    logger.info("Database connections closed")
