"""
TripSaathi Database Models
============================
SQLAlchemy ORM models for users, trips, and itineraries.

WHY ORM MODELS?
--------------
Instead of writing:
    INSERT INTO trips (destination, days, ...) VALUES ('Jaipur', 3, ...)

We write:
    trip = Trip(destination='Jaipur', days=3, ...)
    session.add(trip)
    await session.commit()

Benefits:
1. Type safety — IDE catches field name typos
2. SQL injection prevention — SQLAlchemy parameterizes everything
3. Database-agnostic — works with PostgreSQL, SQLite, MySQL
4. Relationship management — ORM handles JOINs automatically

INTERVIEW QUESTIONS:
- Q: "How does SQLAlchemy prevent SQL injection?"
  A: All values are passed as bound parameters, never string-interpolated.
     `session.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id})`

- Q: "What is relationship() in SQLAlchemy?"
  A: Defines how tables are linked. `Trip.user` gives you the User object
     directly, without writing a JOIN query. SQLAlchemy does the JOIN for you.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def generate_uuid() -> str:
    """Generate a short UUID for trip IDs."""
    return str(uuid.uuid4())[:8]


class User(Base):
    """
    User model — stores basic user info.
    
    Kept simple intentionally. No authentication (would add unnecessary
    complexity for a demo project). In production, you'd use OAuth2/JWT.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationship: one user → many trips
    trips: Mapped[list["Trip"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}')>"


class Trip(Base):
    """
    Trip model — stores a trip planning request and its results.
    
    Each trip corresponds to one invocation of the LangGraph workflow.
    The full itinerary, budget breakdown, and critique are stored as JSON
    in PostgreSQL's native JSON column type.
    """
    __tablename__ = "trips"

    id: Mapped[str] = mapped_column(String(8), primary_key=True, default=generate_uuid)
    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Trip request parameters
    destination: Mapped[str] = mapped_column(String(100), nullable=False)
    days: Mapped[int] = mapped_column(Integer, nullable=False)
    travelers: Mapped[int] = mapped_column(Integer, nullable=False)
    budget: Mapped[float] = mapped_column(Float, nullable=False)
    preferences: Mapped[dict] = mapped_column(JSON, default=list)

    # Workflow results (stored as JSON)
    itinerary: Mapped[dict] = mapped_column(JSON, nullable=True)
    budget_breakdown: Mapped[dict] = mapped_column(JSON, nullable=True)
    critique: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Summary fields for quick queries
    total_estimated_cost: Mapped[float] = mapped_column(Float, nullable=True)
    within_budget: Mapped[bool] = mapped_column(default=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    revision_count: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User | None"] = relationship(back_populates="trips")

    def __repr__(self):
        return f"<Trip(id='{self.id}', destination='{self.destination}', status='{self.status}')>"
