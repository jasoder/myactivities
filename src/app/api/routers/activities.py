from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.activities import (
    ActivitiesResponse,
    ActivityCreate,
    ActivityUpdate,
    ActivityRead,
)
from app.services import activities_service
import uuid
from datetime import datetime
from typing import List

router = APIRouter()


@router.get("/{athlete_id}", response_model=ActivitiesResponse)
async def get_activities_view(
    athlete_id: uuid.UUID,
    start_date: datetime = Query(..., description="Start of the activities"),
    end_date: datetime = Query(..., description="End of the activities"),
    db: AsyncSession = Depends(get_db),
):
    events = await activities_service.get_activities_events(
        db, athlete_id, start_date, end_date
    )
    return ActivitiesResponse(events=events)


@router.post("/", response_model=ActivityRead, status_code=status.HTTP_201_CREATED)
async def create_activity_endpoint(
    activity_in: ActivityCreate, db: AsyncSession = Depends(get_db)
):
    return await activities_service.create_activity(db, activity_in)


@router.get("/athlete/{athlete_id}", response_model=List[ActivityRead])
async def get_activities_by_athlete_endpoint(
    athlete_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    return await activities_service.get_activities_by_athlete(db, athlete_id)


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