from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.athlete import Athlete
from app.db.session import get_db
from app.schemas.errors import ErrorMessage, ErrorResponse

router = APIRouter()

@router.get("/{athlete_id}")
async def get_athlete(athlete_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Athlete).where(Athlete.id == athlete_id))
    athlete = result.scalar_one_or_none()

    if not athlete:
        error = ErrorResponse(detail=[ErrorMessage(msg=f"Athlete with id {athlete_id} not found")])
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.model_dump())

    return athlete

@router.post("/")
async def create_athlete():
    return {"message": "Athlete created"}

@router.put("/")
async def update_athlete():
    return {"message": "Athlete created"}

@router.delete("/")
async def delete_athlete():
    return {"message": "Athlete deleted"}