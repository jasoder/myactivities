from __future__ import annotations
from datetime import datetime, timezone

from sqlalchemy import Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from app.db.base import Base
from app.enums import ActivityType
from models.athlete import Athlete

class CompletedActivity(Base):
    __tablename__ = "completed_activities"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id", ondelete="CASCADE"), index=True)

    external_id: Mapped[str | None] = mapped_column(nullable=True, unique=True, index=True)  # Strava/Intervals id
    name: Mapped[str] = mapped_column(nullable=False)
    type: Mapped[ActivityType] = mapped_column(SAEnum(ActivityType, native_enum=False), nullable=False)

    elapsed_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_date_local: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    planned: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationship (forward reference string is OK too)
    athlete: Mapped["Athlete"] = relationship(back_populates="completed_activities")
