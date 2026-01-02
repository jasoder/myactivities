from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.enums import ActivityType, ActivityGoal

class PlannedActivityBase(BaseModel):
    athlete_id: UUID
    name: str
    type: ActivityType
    goal: Optional[ActivityGoal] = None
    zone: Optional[int] = None
    target_duration: Optional[int] = None
    target_distance: Optional[float] = None
    target_intensity: Optional[float] = None
    scheduled_date: datetime
    completed: bool = False

class PlannedActivityCreate(PlannedActivityBase):
    pass

class PlannedActivityUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[ActivityType] = None
    goal: Optional[ActivityGoal] = None
    zone: Optional[int] = None
    target_duration: Optional[int] = None
    target_distance: Optional[float] = None
    target_intensity: Optional[float] = None
    scheduled_date: Optional[datetime] = None
    completed: Optional[bool] = None
    linked_activity_id: Optional[UUID] = None

class PlannedActivityRead(PlannedActivityBase):
    id: UUID
    linked_activity_id: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)