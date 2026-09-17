from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator

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


class AthleteCreate(AthleteBase):
    """Fields required for creating a new athlete"""
    id: UUID = Field(default_factory=uuid4)


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

    @model_validator(mode="before")
    @classmethod
    def compute_strava_connected(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "strava_connected" not in data:
                data["strava_connected"] = bool(data.get("strava_id") or data.get("access_token"))
            return data
        # For ORM object or MagicMock
        strava_id = getattr(data, "strava_id", None)
        access_token = getattr(data, "access_token", None)
        try:
            if not hasattr(data, "strava_connected") or getattr(data, "strava_connected", None) is None:
                setattr(data, "strava_connected", bool(strava_id or access_token))
        except Exception:
            pass
        return data
        
        
class AthleteCreateResponse(BaseModel):
    id: UUID
    
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