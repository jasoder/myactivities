from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services import planned_activity_service
from app.schemas.planned_activity import (
    PlannedActivityCreate, 
    PlannedActivityRead, 
    PlannedActivityUpdate
)
import uuid
from typing import List

router = APIRouter()

@router.post("/", response_model=PlannedActivityRead, status_code=status.HTTP_201_CREATED)
async def create_planned_activity(
    activity_in: PlannedActivityCreate, 
    db: AsyncSession = Depends(get_db)
):
    return await planned_activity_service.create_planned_activity(db, activity_in)

@router.get("/athlete/{athlete_id}", response_model=List[PlannedActivityRead])
async def get_athlete_plans(athlete_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await planned_activity_service.get_planned_activities_by_athlete(db, athlete_id)

@router.put("/{activity_id}", response_model=PlannedActivityRead)
async def update_planned_activity(
    activity_id: uuid.UUID,
    activity_in: PlannedActivityUpdate,
    db: AsyncSession = Depends(get_db)
):
    activity = await planned_activity_service.get_planned_activity_by_id(db, activity_id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planned activity not found"
        )
    
    return await planned_activity_service.update_planned_activity(
        db, db_activity=activity, activity_in=activity_in
    )

@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(activity_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    activity = await planned_activity_service.get_planned_activity_by_id(db, activity_id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Planned activity not found"
        )
    await planned_activity_service.delete_planned_activity(db, activity)
    return None