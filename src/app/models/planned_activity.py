from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, DateTime, Boolean, Enum, ForeignKey
from models.completed_activity import CompletedActivity
from models.athlete import Athlete
from app.db.base import Base
from enums import ActivityType, ActivityGoal

class PlannedActivity(Base):
    __tablename__ = "planned_activities"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id", ondelete="CASCADE"))
    
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[ActivityType] = mapped_column(Enum(ActivityType), nullable=False)
    goal: Mapped[Optional[ActivityGoal]] = mapped_column(Enum(ActivityGoal), nullable=True)
    zone: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    target_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_distance: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_intensity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    scheduled_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    linked_activity_id: Mapped[Optional[int]] = mapped_column(ForeignKey("completed_activity.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["Athlete"] = relationship(back_populates="planned_activities")
    linked_activity: Mapped[Optional["CompletedActivity"]] = relationship()