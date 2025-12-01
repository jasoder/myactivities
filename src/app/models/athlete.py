from sqlalchemy import String, Integer, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone
from app.db.base import Base
from typing import Optional, TYPE_CHECKING
import uuid
from sqlalchemy.dialects.postgresql import UUID

if TYPE_CHECKING:
    from app.models.completed_activity import CompletedActivity
    from app.models.planned_activity import PlannedActivity
    
class Athlete(Base):
    __tablename__ = "athletes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Performance metrics
    ftp: Mapped[Optional[int]] = mapped_column(Integer)
    threshold_pace: Mapped[Optional[float]] = mapped_column(Float)
    weight: Mapped[Optional[float]] = mapped_column(Float)
    max_hr: Mapped[Optional[int]] = mapped_column(Integer)
    lthr: Mapped[Optional[int]] = mapped_column(Integer)

    # Integrations
    strava_id: Mapped[Optional[str]] = mapped_column(String, unique=True)
    intervals_icu_id: Mapped[Optional[str]] = mapped_column(String, unique=True)
    access_token: Mapped[Optional[str]] = mapped_column(String)
    refresh_token: Mapped[Optional[str]] = mapped_column(String)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Preferences
    preferred_sports: Mapped[Optional[list[str]]] = mapped_column(JSONB)
    timezone: Mapped[Optional[str]] = mapped_column(String, default="UTC")
    weekly_training_hours: Mapped[Optional[float]] = mapped_column(Float)
    ai_enabled: Mapped[bool] = mapped_column(default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    completed_activities: Mapped[list["CompletedActivity"]] = relationship(
        "CompletedActivity", back_populates="athlete", cascade="all, delete"
    )
    planned_activities: Mapped[list["PlannedActivity"]] = relationship(
        "PlannedActivity", back_populates="athlete", cascade="all, delete"
    )
