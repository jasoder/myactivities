from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4

class AthleteBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None

    # Performance metrics
    ftp: Optional[int] = None
    threshold_pace: Optional[float] = None
    weight: Optional[float] = None
    max_hr: Optional[int] = None
    lthr: Optional[int] = None

    # Integrations
    strava_id: Optional[str] = None
    intervals_icu_id: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None

    # Preferences
    preferred_sports: Optional[List[str]] = Field(default_factory=list)
    timezone: Optional[str] = "UTC"
    weekly_training_hours: Optional[float] = None
    ai_enabled: Optional[bool] = True


class AthleteCreate(AthleteBase):
    """Fields required for creating a new athlete"""
    email: EmailStr
    id: UUID  = Field(default_factory=uuid4)


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
    """Fields returned from the API"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        
        
class AthleteCreateResponse(BaseModel):
    id: UUID

    class Config:
        from_attributes = True