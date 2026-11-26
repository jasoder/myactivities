from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class AthleteBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None

    # Performance metrics
    ftp: Optional[int] = None
    threshold_pace: Optional[float] = None
    weight: Optional[float] = None
    max_hr: Optional[int] = None
    lthr: Optional[int] = None

    # Preferences
    preferred_sports: Optional[List[str]] = Field(default_factory=list)
    timezone: Optional[str] = "UTC"
    weekly_training_hours: Optional[float] = None
    ai_enabled: Optional[bool] = True


class AthleteUpdate(BaseModel):
    name: Optional[str] = None
    ftp: Optional[int] = None
    threshold_pace: Optional[float] = None
    weight: Optional[float] = None
    max_hr: Optional[int] = None
    lthr: Optional[int] = None
    preferred_sports: Optional[List[str]] = None
    timezone: Optional[str] = None
    weekly_training_hours: Optional[float] = None
    ai_enabled: Optional[bool] = None


class AthleteRead(AthleteBase):
    """Sanitized, safe public profile of an athlete."""
    id: UUID
    strava_connected: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TrainingPreferenceBase(BaseModel):
    max_days_per_week: int = 7
    sport_targets: dict = Field(default_factory=dict)
    split_notes: Optional[str] = None
    rest_day_preference: Optional[List[str]] = None


class TrainingPreferenceUpdate(BaseModel):
    max_days_per_week: Optional[int] = None
    sport_targets: Optional[dict] = None
    split_notes: Optional[str] = None
    rest_day_preference: Optional[List[str]] = None


class TrainingPreferenceRead(TrainingPreferenceBase):
    athlete_id: UUID
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
