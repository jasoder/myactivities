import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.completed_activity import CompletedActivity
from app.schemas.completed_activity import CompletedActivityCreate, CompletedActivityUpdate


async def get_completed_activities_by_athlete(db: AsyncSession, athlete_id: uuid.UUID):
    result = await db.execute(
        select(CompletedActivity).where(CompletedActivity.athlete_id == athlete_id)
    )
    return result.scalars().all()

async def get_completed_activity_by_id(db: AsyncSession, activity_id: uuid.UUID):
    result = await db.execute(
        select(CompletedActivity).where(CompletedActivity.id == activity_id)
    )
    return result.scalar_one_or_none()

async def create_completed_activity(db: AsyncSession, activity_in: CompletedActivityCreate):
    new_activity = CompletedActivity(**activity_in.model_dump())
    db.add(new_activity)
    await db.commit()
    await db.refresh(new_activity)
    return new_activity

async def delete_completed_activity(db: AsyncSession, activity: CompletedActivity):
    await db.delete(activity)
    await db.commit()

async def update_completed_activity(
    db: AsyncSession,
    db_activity: CompletedActivity,
    activity_in: CompletedActivityUpdate,
) -> CompletedActivity:
    update_data = activity_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_activity, field, value)

    await db.commit()
    await db.refresh(db_activity)
    return db_activity
