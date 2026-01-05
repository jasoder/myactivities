from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.completed_activity import ActivitySource


class CompletedActivityBase(BaseModel):
    athlete_id: UUID
    external_id: Optional[str] = None
    source: ActivitySource
    name: Optional[str] = None
    sport_type: Optional[str] = None
    start_date_local: Optional[datetime] = None


class CompletedActivityCreate(CompletedActivityBase):
    pass


class CompletedActivityUpdate(BaseModel):
    external_id: Optional[str] = None
    name: Optional[str] = None
    sport_type: Optional[str] = None
    start_date_local: Optional[datetime] = None
    source: Optional[ActivitySource] = None


class CompletedActivityRead(CompletedActivityBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
