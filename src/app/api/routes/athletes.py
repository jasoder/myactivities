from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.athlete import Athlete
from app.db.session import get_db
from app.schemas.athlete import AthleteCreate, AthleteUpdate, AthleteRead
from app.schemas.errors import ErrorMessage, ErrorResponse

router = APIRouter()

@router.get("/{athlete_id}", response_model=AthleteRead)
async def get_athlete(athlete_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Athlete).where(Athlete.id == athlete_id))
    athlete = result.scalar_one_or_none()

    if not athlete:
        error = ErrorResponse(detail=[ErrorMessage(msg=f"Athlete with id {athlete_id} not found")])
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.model_dump())

    return athlete


@router.post("/", response_model=AthleteRead, status_code=status.HTTP_201_CREATED)
async def create_athlete(athlete_in: AthleteCreate, db: AsyncSession = Depends(get_db)):
    new_athlete = Athlete(**athlete_in.model_dump())
    db.add(new_athlete)
    await db.commit()
    await db.refresh(new_athlete)
    return new_athlete


@router.put("/{athlete_id}", response_model=AthleteRead)
async def update_athlete(athlete_id: int, athlete_in: AthleteUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Athlete).where(Athlete.id == athlete_id))
    athlete = result.scalar_one_or_none()

    if not athlete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Athlete {athlete_id} not found")

    for field, value in athlete_in.model_dump(exclude_unset=True).items():
        setattr(athlete, field, value)

    await db.commit()
    await db.refresh(athlete)
    return athlete


@router.delete("/{athlete_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_athlete(athlete_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Athlete).where(Athlete.id == athlete_id))
    athlete = result.scalar_one_or_none()

    if not athlete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Athlete {athlete_id} not found")

    await db.delete(athlete)
    await db.commit()
    return None