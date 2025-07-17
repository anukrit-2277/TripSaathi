"""
TripSaathi CRUD Operations
=============================
Database operations for creating, reading, updating trips.

CRUD = Create, Read, Update, Delete

WHY SEPARATE CRUD FROM ROUTES?
-------------------------------
Routes handle HTTP concerns (request parsing, status codes, headers).
CRUD handles database concerns (queries, transactions, data mapping).

This separation means:
- CRUD can be reused from tests, CLI tools, or background jobs
- Routes stay thin and focused on HTTP
- Database logic is testable in isolation
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Trip, User
from app.core.logger import get_logger

logger = get_logger(__name__)


# ============================================================
# Trip CRUD
# ============================================================

async def create_trip(
    db: AsyncSession,
    trip_id: str,
    destination: str,
    days: int,
    travelers: int,
    budget: float,
    preferences: list[str],
    itinerary: dict,
    budget_breakdown: dict,
    critique: dict,
    total_estimated_cost: float,
    within_budget: bool,
    status: str,
    revision_count: int,
    user_id: int | None = None,
) -> Trip:
    """
    Save a completed trip to the database.
    
    Called after the LangGraph workflow completes successfully.
    """
    trip = Trip(
        id=trip_id,
        user_id=user_id,
        destination=destination,
        days=days,
        travelers=travelers,
        budget=budget,
        preferences=preferences,
        itinerary=itinerary,
        budget_breakdown=budget_breakdown,
        critique=critique,
        total_estimated_cost=total_estimated_cost,
        within_budget=within_budget,
        status=status,
        revision_count=revision_count,
    )

    db.add(trip)
    await db.commit()
    await db.refresh(trip)

    logger.info(f"💾 Trip saved: {trip.id} ({trip.destination})")
    return trip


async def get_trip_by_id(db: AsyncSession, trip_id: str) -> Trip | None:
    """Retrieve a trip by its ID."""
    result = await db.execute(
        select(Trip).where(Trip.id == trip_id)
    )
    return result.scalar_one_or_none()


async def get_recent_trips(
    db: AsyncSession,
    limit: int = 10,
    user_id: int | None = None,
) -> list[Trip]:
    """Get the most recent trips, optionally filtered by user."""
    query = select(Trip).order_by(Trip.created_at.desc()).limit(limit)

    if user_id is not None:
        query = query.where(Trip.user_id == user_id)

    result = await db.execute(query)
    return list(result.scalars().all())


# ============================================================
# User CRUD
# ============================================================

async def get_or_create_user(
    db: AsyncSession,
    name: str,
    email: str,
) -> User:
    """Get existing user by email, or create a new one."""
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if user is None:
        user = User(name=name, email=email)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"👤 New user created: {user.name} ({user.email})")
    
    return user
