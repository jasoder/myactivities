from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.athlete import (
    AthleteCreate,
    AthleteUpdate,
    AthleteRead,
    AthleteCreateResponse,
    TrainingPreferenceRead,
    TrainingPreferenceUpdate,
)
from app.services import athlete_service
import uuid

from app.services.auth_service import get_current_athlete
from app.models.athlete import Athlete

router = APIRouter()

@router.get("/me", response_model=AthleteRead)
async def get_current_athlete_profile(
    current_athlete: Athlete = Depends(get_current_athlete),
):
    """Get profile of current authenticated athlete."""
    return current_athlete

@router.get("/{athlete_id}", response_model=AthleteRead)
async def get_athlete(athlete_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    athlete = await athlete_service.get_athlete_by_id(db, athlete_id)

    if not athlete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Athlete with id {athlete_id} not found")

    return athlete


@router.post("/", response_model=AthleteCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_athlete(athlete_in: AthleteCreate, db: AsyncSession = Depends(get_db)):
    return await athlete_service.create_new_athlete(db, athlete_in)


@router.put("/{athlete_id}", response_model=AthleteRead)
async def update_athlete(athlete_id: uuid.UUID, athlete_in: AthleteUpdate, db: AsyncSession = Depends(get_db)):
    
    athlete = await athlete_service.get_athlete_by_id(db, athlete_id)

    if not athlete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Athlete {athlete_id} not found")

    updated_athlete = await athlete_service.update_existing_athlete(db, athlete, athlete_in)
    
    return updated_athlete

@router.delete("/{athlete_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_athlete(athlete_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    deleted = await athlete_service.delete_athlete_by_id(db, athlete_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Athlete with id {athlete_id} not found"
        )
    
    return None


@router.get("/{athlete_id}/preferences", response_model=TrainingPreferenceRead)
async def get_athlete_preferences(athlete_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get training preferences for athlete, creating default if not yet existing."""
    athlete = await athlete_service.get_athlete_by_id(db, athlete_id)
    if not athlete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Athlete not found")
    return await athlete_service.get_or_create_training_preferences(db, athlete_id)


@router.put("/{athlete_id}/preferences", response_model=TrainingPreferenceRead)
async def update_athlete_preferences(
    athlete_id: uuid.UUID,
    pref_in: TrainingPreferenceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update training preferences for athlete."""
    athlete = await athlete_service.get_athlete_by_id(db, athlete_id)
    if not athlete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Athlete not found")
    return await athlete_service.update_training_preferences(db, athlete_id, pref_in)