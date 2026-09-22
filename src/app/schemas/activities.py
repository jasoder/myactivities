from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional, Literal, Dict, Any, List
from app.models.activities import ActivityStatus
from app.enums import ActivitySource


class ActivityMetricBase(BaseModel):
    distance_m: Optional[float] = None
    duration_min: Optional[int] = None
    elevation_gain_m: Optional[float] = None
    average_speed_mps: Optional[float] = None
    average_hr_bpm: Optional[float] = None
    max_hr_bpm: Optional[float] = None
    average_power_w: Optional[float] = None
    calories_kcal: Optional[float] = None
    device_name: Optional[str] = None


class ActivityMetricCreate(ActivityMetricBase):
    pass


class ActivityMetricRead(ActivityMetricBase):
    activity_id: UUID

    model_config = ConfigDict(from_attributes=True)


class ActivityBase(BaseModel):
    athlete_id: UUID
    source: ActivitySource
    status: ActivityStatus = ActivityStatus.planned
    sport_type: Optional[str] = None
    planned_date: Optional[datetime] = None
    actual_date: Optional[datetime] = None
    name: Optional[str] = None
    description: Optional[str] = None
    duration_min: Optional[int] = None
    distance_m: Optional[float] = None
    intensity: Optional[float] = None
    week_plan_id: Optional[UUID] = None
    matched_strava_activity_id: Optional[str] = None
    reconciliation_note: Optional[str] = None
    plan_metadata: Optional[Dict[str, Any]] = None


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(BaseModel):
    status: Optional[ActivityStatus] = None
    sport_type: Optional[str] = None
    planned_date: Optional[datetime] = None
    actual_date: Optional[datetime] = None
    name: Optional[str] = None
    description: Optional[str] = None
    duration_min: Optional[int] = None
    distance_m: Optional[float] = None
    intensity: Optional[float] = None
    week_plan_id: Optional[UUID] = None
    matched_strava_activity_id: Optional[str] = None
    reconciliation_note: Optional[str] = None
    plan_metadata: Optional[Dict[str, Any]] = None


class ActivityRead(ActivityBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    metrics: Optional[ActivityMetricRead] = None

    model_config = ConfigDict(from_attributes=True)


class ActivitiesSummary(BaseModel):
    distance_m: Optional[float] = None
    duration_s: Optional[int] = None
    training_load: Optional[float] = None


class ActivitiesEntry(BaseModel):
    id: UUID
    date: datetime
    title: Optional[str] = "Untitled Activity"
    type: Optional[str] = "Other"
    status: Literal["planned", "completed", "missed", "modified"]
    data: ActivitiesSummary


class ActivitiesResponse(BaseModel):
    events: list[ActivitiesEntry]


class ConfirmWeekPlanWorkout(BaseModel):
    day_offset: int = 0
    planned_date: Optional[datetime] = None
    name: str = "Base Endurance Run"
    sport_type: str = "Run"
    duration_min: Optional[int] = 60
    distance_m: Optional[float] = None
    target_distance_m: Optional[float] = None
    intensity: Optional[float] = None
    target_intensity: Optional[float] = None
    description: Optional[str] = "Zone 2 aerobic base stimulus"
    plan_metadata: Optional[Dict[str, Any]] = None


class ConfirmPlanRequest(BaseModel):
    athlete_id: UUID
    start_date: Optional[datetime] = None
    week_start_date: Optional[datetime] = None
    duration_days: Optional[int] = 7
    reasoning: Optional[str] = "Adaptive training plan"
    workouts: List[ConfirmWeekPlanWorkout]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "athlete_id": "00000000-0000-0000-0000-000000000000",
                "start_date": "2026-09-08T00:00:00Z",
                "duration_days": 28,
                "reasoning": "4-week periodized build block with deload",
                "workouts": [
                    {
                        "day_offset": 0,
                        "planned_date": "2026-09-08T08:00:00Z",
                        "name": "Base Endurance Run",
                        "sport_type": "Run",
                        "duration_min": 60,
                        "distance_m": 10000.0,
                        "intensity": 70.0,
                        "description": "Zone 2 aerobic pace",
                    }
                ],
            }
        }
    )


ConfirmWeekPlanRequest = ConfirmPlanRequest



