from __future__ import annotations

from typing import Optional
from datetime import datetime, timezone
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, Integer, Float, DateTime, Boolean, Enum, ForeignKey

from app.db.base import Base
from app.enums import ActivityType, ActivityGoal
from app.models.completed_activity import CompletedActivity
from app.models.athlete import Athlete


class PlannedActivity(Base):
    __tablename__ = "planned_activities"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletes.id", ondelete="CASCADE")
    )
    athlete: Mapped["Athlete"] = relationship("Athlete", back_populates="planned_activities")

    linked_activity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("completed_activities.id"), nullable=True
    )

    linked_activity: Mapped[Optional["CompletedActivity"]] = relationship(
        "CompletedActivity",
        foreign_keys=[linked_activity_id],
    )
    
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[ActivityType] = mapped_column(Enum(ActivityType), nullable=False)
    goal: Mapped[Optional[ActivityGoal]] = mapped_column(Enum(ActivityGoal), nullable=True)
    zone: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    target_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_distance: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_intensity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    scheduled_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    completed: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<PlannedActivity(id={self.id}, name='{self.name}', type={self.type}, date={self.scheduled_date})>"