from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.db.session import get_db
from app.models.athlete import Athlete
from app.services.auth_service import get_optional_current_athlete
from app.schemas.activities import (
    ActivityCreate,
    ActivityUpdate,
    ActivityRead,
)
from app.services import activities_service
import uuid

router = APIRouter()


@router.post("/", response_model=ActivityRead, status_code=status.HTTP_201_CREATED)
async def create_activity_endpoint(
    activity_in: ActivityCreate,
    current_athlete: Optional[Athlete] = Depends(get_optional_current_athlete),
    db: AsyncSession = Depends(get_db),
):
    """Create a new planned or completed activity."""
    target_athlete_id = activity_in.athlete_id or (current_athlete.id if current_athlete else None)
    if not target_athlete_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="athlete_id or Bearer authentication is required.",
        )
    if activity_in.athlete_id != target_athlete_id:
        activity_in.athlete_id = target_athlete_id
    return await activities_service.create_activity(db, activity_in)



@router.get("/detail/{activity_id}", response_model=ActivityRead)
async def get_activity_detail_endpoint(
    activity_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    activity = await activities_service.get_activity_by_id(db, activity_id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found"
        )
    return activity


@router.put("/{activity_id}", response_model=ActivityRead)
async def update_activity_endpoint(
    activity_id: uuid.UUID,
    activity_in: ActivityUpdate,
    db: AsyncSession = Depends(get_db),
):
    db_activity = await activities_service.get_activity_by_id(db, activity_id)
    if not db_activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found"
        )
    return await activities_service.update_activity(db, db_activity, activity_in)


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity_endpoint(
    activity_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    db_activity = await activities_service.get_activity_by_id(db, activity_id)
    if not db_activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found"
        )
    await activities_service.delete_activity(db, db_activity)
    return None