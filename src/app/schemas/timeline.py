from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional, Literal

class TimelineSummary(BaseModel):
    distance_m: Optional[float] = None
    duration_s: Optional[int] = None
    training_load: Optional[float] = None

class TimelineEntry(BaseModel):
    id: UUID
    date: datetime
    title: Optional[str] = "Untitled Activity"
    type: Optional[str] = "Other"
    status: Literal["planned", "completed", "missed"]
    data: TimelineSummary

class TimelineResponse(BaseModel):
    events: list[TimelineEntry]
