from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from ...schemas.activities import ActivitiesResponse
from app.services import activities_service
import uuid
from datetime import datetime

router = APIRouter()

@router.get("/{athlete_id}", response_model=ActivitiesResponse)
async def get_activities_view(
    athlete_id: uuid.UUID,
    start_date: datetime = Query(..., description="Start of the activities"),
    end_date: datetime = Query(..., description="End of the activities"),
    db: AsyncSession = Depends(get_db)
):
    events = await activities_service.get_activities_events(db, athlete_id, start_date, end_date)
    return ActivitiesResponse(events=events)