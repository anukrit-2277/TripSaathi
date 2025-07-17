"""
TripSaathi Database Configuration
====================================
Sets up SQLAlchemy async engine, session factory, and connection management.

WHY SQLALCHEMY + ASYNC?
-----------------------
1. SQLAlchemy ORM: Write Python classes instead of raw SQL. Prevents SQL
   injection, provides type safety, and makes queries database-agnostic.

2. Async (asyncpg): FastAPI is async, so our DB driver must be async too.
   Otherwise, every DB query blocks the event loop and kills performance.

3. Connection Pooling: Instead of opening a new DB connection per request
   (expensive!), we maintain a pool of reusable connections.

INTERVIEW QUESTIONS:
- Q: "What is connection pooling?"
  A: Creating a DB connection takes ~50ms (TCP handshake, authentication).
     A pool pre-creates connections and reuses them. Our pool keeps 5-20
     connections ready, serving them to requests instantly.

- Q: "Why async DB driver?"
  A: FastAPI handles requests concurrently with async/await. If the DB driver
     is synchronous, `await db.execute(query)` blocks the entire event loop.
     With asyncpg, the event loop continues processing other requests while
     waiting for the DB response.

- Q: "SQLAlchemy 2.0 vs 1.x?"
  A: 2.0 uses modern Python async patterns, type hints, and a cleaner API.
     The select() syntax replaces the old Query() API.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


# DeclarativeBase is the modern SQLAlchemy 2.0 way to define a base class.
# All ORM models inherit from this.
class Base(DeclarativeBase):
    pass


# Create the async engine
# pool_size=5: Keep 5 connections ready at all times
# max_overflow=10: Allow up to 10 extra connections under heavy load
# echo=False: Don't log every SQL query (too noisy in production)
engine = create_async_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=10,
    echo=False,
)

# Session factory: creates AsyncSession instances
# expire_on_commit=False: Prevents "lazy load" errors after commit
# (with async, lazy loading doesn't work — you'd get a "greenlet" error)
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """
    Dependency injection for FastAPI routes.
    
    Usage in routes:
        @router.get("/trips")
        async def list_trips(db: AsyncSession = Depends(get_db)):
            ...
    
    The `async with` ensures the session is properly closed after the request,
    even if an exception occurs.
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """
    Create all database tables.
    Called once during app startup.
    """
    async with engine.begin() as conn:
        # Import models so Base knows about them
        from app.db import models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables created")


async def close_db():
    """
    Close the database engine and all connections.
    Called during app shutdown.
    """
    await engine.dispose()
    logger.info("🛑 Database connections closed")
