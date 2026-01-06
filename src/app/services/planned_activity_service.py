import uuid
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.planned_activity import PlannedActivity
from app.schemas.planned_activity import PlannedActivityCreate, PlannedActivityUpdate
from datetime import datetime

async def get_planned_activities_by_athlete(db: AsyncSession, athlete_id: uuid.UUID):
    result = await db.execute(
        select(PlannedActivity).where(PlannedActivity.athlete_id == athlete_id)
    )
    return result.scalars().all()

async def get_planned_activity_by_id(db: AsyncSession, activity_id: uuid.UUID):
    result = await db.execute(
        select(PlannedActivity).where(PlannedActivity.id == activity_id)
    )
    return result.scalar_one_or_none()


async def get_planned_activities_by_date_range(
    db: AsyncSession, athlete_id: uuid.UUID, start_date: datetime, end_date: datetime
):
    result = await db.execute(
        select(PlannedActivity).where(
            PlannedActivity.athlete_id == athlete_id,
            PlannedActivity.scheduled_date >= start_date,
            PlannedActivity.scheduled_date <= end_date,
        )
    )
    return result.scalars().all()

async def create_planned_activity(db: AsyncSession, activity_in: PlannedActivityCreate):
    new_activity = PlannedActivity(**activity_in.model_dump())
    db.add(new_activity)
    await db.commit()
    await db.refresh(new_activity)
    return new_activity

async def delete_planned_activity(db: AsyncSession, activity: PlannedActivity):
    await db.delete(activity)
    await db.commit()
    
async def update_planned_activity(
    db: AsyncSession, 
    db_activity: PlannedActivity, 
    activity_in: PlannedActivityUpdate
) -> PlannedActivity:
    update_data = activity_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_activity, field, value)
    
    await db.commit()
    await db.refresh(db_activity)
    return db_activity