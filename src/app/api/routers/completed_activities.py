from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services import completed_activity_service
from app.schemas.completed_activity import (
    CompletedActivityCreate,
    CompletedActivityRead,
    CompletedActivityUpdate,
)
import uuid
from typing import List

router = APIRouter()


@router.post("/", response_model=CompletedActivityRead, status_code=status.HTTP_201_CREATED)
async def create_completed_activity(
    activity_in: CompletedActivityCreate, db: AsyncSession = Depends(get_db)
):
    return await completed_activity_service.create_completed_activity(db, activity_in)


@router.get("/athlete/{athlete_id}", response_model=List[CompletedActivityRead])
async def get_athlete_completed(athlete_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await completed_activity_service.get_completed_activities_by_athlete(db, athlete_id)


@router.put("/{activity_id}", response_model=CompletedActivityRead)
async def update_completed_activity(
    activity_id: uuid.UUID,
    activity_in: CompletedActivityUpdate,
    db: AsyncSession = Depends(get_db),
):
    activity = await completed_activity_service.get_completed_activity_by_id(db, activity_id)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Completed activity not found")

    return await completed_activity_service.update_completed_activity(
        db, db_activity=activity, activity_in=activity_in
    )


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_completed(activity_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    activity = await completed_activity_service.get_completed_activity_by_id(db, activity_id)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Completed activity not found")

    await completed_activity_service.delete_completed_activity(db, activity)
    return None