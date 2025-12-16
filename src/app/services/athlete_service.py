import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.athlete import Athlete
from app.schemas.athlete import AthleteCreate, AthleteUpdate

async def get_athlete_by_id(db: AsyncSession, athlete_id: uuid.UUID) -> Athlete | None:
    result = await db.execute(select(Athlete).where(Athlete.id == athlete_id))
    
    return result.scalar_one_or_none()

async def create_new_athlete(db: AsyncSession, athlete_in: AthleteCreate) -> Athlete:
    new_athlete = Athlete(**athlete_in.model_dump())
    db.add(new_athlete)
    await db.commit()
    await db.refresh(new_athlete)
    
    return new_athlete

async def update_existing_athlete(db: AsyncSession, athlete: Athlete, athlete_in: AthleteUpdate) -> Athlete:
    for field, value in athlete_in.model_dump(exclude_unset=True).items():
        setattr(athlete, field, value)
    
    await db.commit()
    await db.refresh(athlete)
    
    return athlete