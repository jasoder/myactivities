from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from ...schemas.timeline import TimelineResponse
from app.services import timeline_service
import uuid
from datetime import datetime

router = APIRouter()

@router.get("/{athlete_id}", response_model=TimelineResponse)
async def get_timeline_view(
    athlete_id: uuid.UUID,
    start_date: datetime = Query(..., description="Start of the timeline"),
    end_date: datetime = Query(..., description="End of the timeline"),
    db: AsyncSession = Depends(get_db)
):
    events = await timeline_service.get_timeline_events(db, athlete_id, start_date, end_date)
    return TimelineResponse(events=events)