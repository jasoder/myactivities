from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, Float, Integer, DateTime, Boolean, Enum
from app.db.base import Base
from app.enums import ActivityType
from app.enums import ActivityGoal
from app.models.completedActivity import CompletedActivity
from app.models.athlete import Athlete

class PlannedActivity(Base):
    __tablename__ = "planned_activities"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("Athlete.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[ActivityType] = mapped_column(Enum(ActivityType), nullable=False)
    goal: Mapped[ActivityGoal | None] = mapped_column(Enum(ActivityGoal), nullable=True)
    zone: Mapped[int] = mapped_column(Integer, nullable=True)

    # planned parameters
    target_duration: Mapped[int] = mapped_column(Integer, nullable=True)  # seconds or minutes
    target_distance: Mapped[float] = mapped_column(Float, nullable=True)  # km
    target_intensity: Mapped[float] = mapped_column(Float, nullable=True)  # e.g., RPE 1–10 or %FTP or zone
    scheduled_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    linked_activity_id: Mapped[int | None] = mapped_column(ForeignKey("activitys.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["Athlete"] = relationship(back_populates="planned_activities")
    linked_activity: Mapped["CompletedActivity"] = relationship()
