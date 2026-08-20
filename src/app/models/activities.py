from __future__ import annotations

import uuid
import enum
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from sqlalchemy import String, Float, Integer, Boolean, DateTime, Text, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.enums import ActivitySource
from app.models.athlete import Athlete


class ActivityStatus(enum.Enum):
    planned = "planned"
    completed = "completed"
    missed = "missed"
    modified = "modified"


class Activity(Base):
    """
    Unified activities table that replaces the separate completed_activities
    and planned_activities tables. Handles both planned workouts and logged
    activities in a single table for efficient calendar querying.
    """
    __tablename__ = "activities"

    # Core identifiers
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    athlete_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletes.id", ondelete="CASCADE")
    )
    athlete: Mapped["Athlete"] = relationship("Athlete", back_populates="activities")

    external_id: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True)
    strava_activity_id: Mapped[Optional[str]] = mapped_column(String, unique=True)
    intervals_activity_id: Mapped[Optional[str]] = mapped_column(String, unique=True)

    # Phase 1 required fields
    source: Mapped[ActivitySource] = mapped_column(Enum(ActivitySource), nullable=False)
    status: Mapped[ActivityStatus] = mapped_column(
        Enum(ActivityStatus), nullable=False, default=ActivityStatus.planned
    )
    sport_type: Mapped[Optional[str]] = mapped_column(String)

    # Date tracking (planned_date vs actual_date as specified)
    planned_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    actual_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Plan metadata from Claude (target duration, intensity, structure, reasoning)
    plan_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, default=dict)

    # Reconciliation support
    reconciliation_note: Mapped[Optional[str]] = mapped_column(Text)
    matched_strava_activity_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Week plan linking (groups activities planned together for scoping replans)
    week_plan_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("week_plans.id", ondelete="SET NULL"), nullable=True
    )

    # Activity naming/description
    name: Mapped[Optional[str]] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Duration/intensity
    duration_min: Mapped[Optional[int]] = mapped_column(Integer)
    distance_m: Mapped[Optional[float]] = mapped_column(Float)
    intensity: Mapped[Optional[float]] = mapped_column(Float)

    # Metrics (for completed activities)
    elevation_gain_m: Mapped[Optional[float]] = mapped_column(Float)
    elevation_loss_m: Mapped[Optional[float]] = mapped_column(Float)
    average_speed_mps: Mapped[Optional[float]] = mapped_column(Float)
    max_speed_mps: Mapped[Optional[float]] = mapped_column(Float)
    average_cadence: Mapped[Optional[float]] = mapped_column(Float)
    average_hr_bpm: Mapped[Optional[float]] = mapped_column(Float)
    max_hr_bpm: Mapped[Optional[float]] = mapped_column(Float)
    average_power_w: Mapped[Optional[float]] = mapped_column(Float)
    max_power_w: Mapped[Optional[float]] = mapped_column(Float)
    calories_kcal: Mapped[Optional[float]] = mapped_column(Float)

    # Device & gear
    device_name: Mapped[Optional[str]] = mapped_column(String)
    gear_id: Mapped[Optional[str]] = mapped_column(String)
    gear_name: Mapped[Optional[str]] = mapped_column(String)

    # Sync & housekeeping
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )
    last_sync: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    analyzed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Links
    strava_url: Mapped[Optional[str]] = mapped_column(String)
    intervals_url: Mapped[Optional[str]] = mapped_column(String)

    def __repr__(self) -> str:
        return (
            f"<Activity(id={self.id}, source={self.source}, "
            f"status={self.status}, sport={self.sport_type})>"
        )


class WeekPlan(Base):
    """
    Groups the 7 planned rows generated together by Claude's planning service.
    Allows scoping replans to 'everything in this week_plan not yet reconciled'.
    """
    __tablename__ = "week_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    athlete_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletes.id", ondelete="CASCADE")
    )
    athlete: Mapped["Athlete"] = relationship("Athlete", back_populates="week_plans")

    activities: Mapped[List["Activity"]] = relationship(
        "Activity", back_populates="week_plan", cascade="all, delete-orphan"
    )

    week_start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="draft",
        comment="draft, confirmed, partially_replanned"
    )

    ai_reasoning: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<WeekPlan(id={self.id}, status={self.status}, week_start={self.week_start_date})>"


class TrainingPreference(Base):
    """
    One row per athlete storing training preferences.
    Used by the Claude planning service to understand user constraints.
    """
    __tablename__ = "training_preferences"

    athlete_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletes.id", ondelete="CASCADE"), primary_key=True
    )
    athlete: Mapped["Athlete"] = relationship("Athlete", back_populates="training_preferences")

    max_days_per_week: Mapped[int] = mapped_column(Integer, default=7)

    # Flexible JSON structure:
    # [
    #   {"sport_type": "strength", "sessions_per_week": 3, "notes": "upper/lower split"},
    #   {"sport_type": "run_or_ride", "sessions_per_week": null, "notes": "every other day"}
    # ]
    sport_targets: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)

    split_notes: Mapped[Optional[str]] = mapped_column(Text)

    # Optional fixed rest days: ["monday", "wednesday"] or null for AI to decide
    rest_day_preference: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<TrainingPreference(athlete={self.athlete_id}, max_days={self.max_days_per_week})>"
