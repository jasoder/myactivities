from datetime import datetime
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.athlete import Athlete
from app.schemas.athlete import (
    AthleteRead,
    AthleteUpdate,
    TrainingPreferenceRead,
    TrainingPreferenceUpdate,
)
from app.schemas.activities import ActivitiesResponse
from app.services.auth_service import get_current_athlete
from app.services import athlete_service, activities_service

router = APIRouter()


@router.get("", response_model=AthleteRead)
@router.get("/", response_model=AthleteRead, include_in_schema=False)
async def get_current_user_profile(
    current_athlete: Athlete = Depends(get_current_athlete),
):
    """Get profile of the currently authenticated user."""
    return current_athlete


@router.put("", response_model=AthleteRead)
@router.put("/", response_model=AthleteRead, include_in_schema=False)
async def update_current_user_profile(
    athlete_in: AthleteUpdate,
    current_athlete: Athlete = Depends(get_current_athlete),
    db: AsyncSession = Depends(get_db),
):
    """Update profile of the currently authenticated user."""
    return await athlete_service.update_existing_athlete(db, current_athlete, athlete_in)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
async def delete_current_user_account(
    current_athlete: Athlete = Depends(get_current_athlete),
    db: AsyncSession = Depends(get_db),
):
    """Delete the authenticated user's account and associated data."""
    await athlete_service.delete_athlete_by_id(db, current_athlete.id)
    return None


@router.delete("/strava", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_user_strava(
    current_athlete: Athlete = Depends(get_current_athlete),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect Strava integration from the authenticated user's account."""
    await athlete_service.disconnect_strava(db, current_athlete)
    return None



@router.get("/preferences", response_model=TrainingPreferenceRead)
async def get_user_training_preferences(
    current_athlete: Athlete = Depends(get_current_athlete),
    db: AsyncSession = Depends(get_db),
):
    """Get training preferences for the authenticated user."""
    return await athlete_service.get_or_create_training_preferences(db, current_athlete.id)


@router.put("/preferences", response_model=TrainingPreferenceRead)
async def update_user_training_preferences(
    pref_in: TrainingPreferenceUpdate,
    current_athlete: Athlete = Depends(get_current_athlete),
    db: AsyncSession = Depends(get_db),
):
    """Update training preferences for the authenticated user."""
    return await athlete_service.update_training_preferences(db, current_athlete.id, pref_in)


@router.get("/activities", response_model=ActivitiesResponse)
async def get_current_user_activities(
    start_date: datetime = Query(..., description="Start of date range"),
    end_date: datetime = Query(..., description="End of date range"),
    current_athlete: Athlete = Depends(get_current_athlete),
    db: AsyncSession = Depends(get_db),
):
    """Get activity events for the authenticated user within the date range (for calendar view)."""
    events = await activities_service.get_activities_events(
        db, current_athlete.id, start_date, end_date
    )
    return ActivitiesResponse(events=events)

