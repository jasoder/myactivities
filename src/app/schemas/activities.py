from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional, Literal

class ActivitiesSummary(BaseModel):
    distance_m: Optional[float] = None
    duration_s: Optional[int] = None
    training_load: Optional[float] = None

class ActivitiesEntry(BaseModel):
    id: UUID
    date: datetime
    title: Optional[str] = "Untitled Activity"
    type: Optional[str] = "Other"
    status: Literal["planned", "completed", "missed"]
    data: ActivitiesSummary

class ActivitiesResponse(BaseModel):
    events: list[ActivitiesEntry]
