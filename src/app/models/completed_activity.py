from __future__ import annotations

import uuid
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Float, Integer, Boolean, DateTime, Text, Enum, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.athlete import Athlete
from app.db.base import Base


class ActivitySource(enum.Enum):
    STRAVA = "strava"
    INTERVALS = "intervals"


class CompletedActivity(Base):
    __tablename__ = "completed_activities"

    # Core identifiers
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletes.id", ondelete="CASCADE")
    )
    athlete: Mapped["Athlete"] = relationship("Athlete", back_populates="completed_activities")
    external_id: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True)
    strava_id: Mapped[Optional[str]] = mapped_column(String, unique=True)
    intervals_id: Mapped[Optional[str]] = mapped_column(String, unique=True)
    source: Mapped[ActivitySource] = mapped_column(Enum(ActivitySource), nullable=False)

    # Metadata
    name: Mapped[Optional[str]] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(Text)
    sport_type: Mapped[Optional[str]] = mapped_column(String)
    sub_type: Mapped[Optional[str]] = mapped_column(String)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    start_date_local: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    timezone: Mapped[Optional[str]] = mapped_column(String)
    trainer: Mapped[Optional[bool]] = mapped_column(Boolean)
    commute: Mapped[Optional[bool]] = mapped_column(Boolean)
    race: Mapped[Optional[bool]] = mapped_column(Boolean)

    # Summary metrics
    distance_m: Mapped[Optional[float]] = mapped_column(Float)
    elapsed_time_s: Mapped[Optional[int]] = mapped_column(Integer)
    moving_time_s: Mapped[Optional[int]] = mapped_column(Integer)
    elevation_gain_m: Mapped[Optional[float]] = mapped_column(Float)
    elevation_loss_m: Mapped[Optional[float]] = mapped_column(Float)
    average_speed_mps: Mapped[Optional[float]] = mapped_column(Float)
    max_speed_mps: Mapped[Optional[float]] = mapped_column(Float)
    average_cadence: Mapped[Optional[float]] = mapped_column(Float)
    average_temp_c: Mapped[Optional[float]] = mapped_column(Float)
    max_temp_c: Mapped[Optional[float]] = mapped_column(Float)
    min_temp_c: Mapped[Optional[float]] = mapped_column(Float)
    average_hr_bpm: Mapped[Optional[float]] = mapped_column(Float)
    max_hr_bpm: Mapped[Optional[float]] = mapped_column(Float)
    average_power_w: Mapped[Optional[float]] = mapped_column(Float)
    weighted_power_w: Mapped[Optional[float]] = mapped_column(Float)
    max_power_w: Mapped[Optional[float]] = mapped_column(Float)
    calories_kcal: Mapped[Optional[float]] = mapped_column(Float)
    carbs_used_g: Mapped[Optional[float]] = mapped_column(Float)

    # Intervals.icu-specific metrics
    icu_training_load: Mapped[Optional[float]] = mapped_column(Float)
    icu_trimp: Mapped[Optional[float]] = mapped_column(Float)
    icu_intensity: Mapped[Optional[float]] = mapped_column(Float)
    icu_efficiency_factor: Mapped[Optional[float]] = mapped_column(Float)
    icu_variability_index: Mapped[Optional[float]] = mapped_column(Float)
    icu_joules: Mapped[Optional[float]] = mapped_column(Float)
    icu_rpe: Mapped[Optional[float]] = mapped_column(Float)

    # Device & gear
    device_name: Mapped[Optional[str]] = mapped_column(String)
    gear_id: Mapped[Optional[str]] = mapped_column(String)
    gear_name: Mapped[Optional[str]] = mapped_column(String)
    gear_distance_m: Mapped[Optional[float]] = mapped_column(Float)

    # Sync & housekeeping
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )
    last_sync: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    icu_sync_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    strava_sync_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    analyzed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Links
    strava_url: Mapped[Optional[str]] = mapped_column(String)
    intervals_url: Mapped[Optional[str]] = mapped_column(String)

    def __repr__(self) -> str:
        return (
            f"<CompletedActivity(id={self.id}, source={self.source}, "
            f"sport={self.sport_type}, date={self.start_date_local})>"
        )