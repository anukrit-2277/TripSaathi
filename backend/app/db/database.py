"""
TripSaathi Database Configuration
====================================
Sets up SQLAlchemy async engine, session factory, and connection management.
"""

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    pass


# libpq query parameters that asyncpg's connect() does not accept. Neon and
# Supabase both hand out URLs carrying these; passed through untouched they
# surface as "connect() got an unexpected keyword argument 'sslmode'" on the
# first query rather than as anything legible at startup.
_LIBPQ_ONLY_PARAMS = frozenset({
    "sslmode",
    "channel_binding",
    "sslrootcert",
    "sslcert",
    "sslkey",
})


def _get_database_url() -> tuple[str, dict]:
    """
    Normalise DATABASE_URL into (url, connect_args) for the asyncpg driver.

    The URL always comes from the environment — never hardcoded — so it has to
    survive whatever shape the provider hands out. Three things happen here:

    1. The driver is forced to asyncpg. Railway, Neon and Supabase all give out
       `postgresql://` (or the legacy `postgres://`), which SQLAlchemy would
       otherwise route to psycopg2, a driver we do not install.

    2. libpq-only query parameters are stripped, and `sslmode` is translated
       into asyncpg's `ssl` connect argument — same vocabulary ("require",
       "verify-full", ...), different keyword. `channel_binding` is dropped
       outright: asyncpg negotiates SCRAM channel binding on its own.

    3. Prepared-statement caching is switched off against a pgbouncer pooler.
       Neon's `-pooler` endpoints run in transaction pooling mode, where a
       cached prepared statement can be reused on a backend connection that
       never declared it — a DuplicatePreparedStatementError that only shows
       up under concurrency, which is the worst way to find it.

    Returns:
        (sqlalchemy_url, connect_args) ready to hand to create_async_engine.
    """
    raw = settings.database_url

    for prefix in ("postgresql+asyncpg://", "postgresql://", "postgres://"):
        if raw.startswith(prefix):
            raw = "postgresql+asyncpg://" + raw[len(prefix):]
            break

    parts = urlsplit(raw)
    connect_args: dict = {}
    kept: list[tuple[str, str]] = []

    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        name = key.lower()
        if name == "sslmode":
            # "disable" means no TLS at all, which is asyncpg's default —
            # setting ssl=disable explicitly would be redundant.
            if value.lower() != "disable":
                connect_args["ssl"] = value.lower()
        elif name in _LIBPQ_ONLY_PARAMS:
            continue
        else:
            kept.append((key, value))

    # asyncpg waits 60s by default. When the database is unreachable — a
    # network that blocks outbound 5432, a paused Neon compute — that turns
    # every request into a minute-long stall before the save is abandoned.
    # Failing fast keeps the itinerary flowing; it just comes back with
    # shareable=False.
    connect_args.setdefault("timeout", 10)

    if "-pooler." in parts.netloc or "pgbouncer" in parts.query.lower():
        # asyncpg's own cache, and SQLAlchemy's dialect-level cache above it.
        connect_args["statement_cache_size"] = 0
        kept.append(("prepared_statement_cache_size", "0"))

    url = urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(kept), parts.fragment)
    )
    return url, connect_args


# Lazy initialization — engine and session are created on first use,
# not at import time. This prevents crashes if DATABASE_URL is invalid.
_engine = None
_async_session = None


def _get_engine():
    global _engine
    if _engine is None:
        url, connect_args = _get_database_url()
        _engine = create_async_engine(
            url,
            pool_size=5,
            max_overflow=10,
            # Serverless Postgres (Neon, Supabase) drops idle connections and
            # autosuspends the compute. Without a pre-ping, the first request
            # after a quiet spell dies on a stale socket instead of quietly
            # reconnecting.
            pool_pre_ping=True,
            echo=False,
            connect_args=connect_args,
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
