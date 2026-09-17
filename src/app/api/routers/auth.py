from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.athlete import Athlete
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.schemas.athlete import AthleteRead
from app.services.auth_service import (
    register_user,
    authenticate_user,
    get_current_athlete,
)

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_endpoint(
    register_in: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new athlete with email and password."""
    athlete, token = await register_user(db, register_in)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        athlete=AthleteRead.model_validate(athlete),
    )


@router.post("/login", response_model=TokenResponse)
async def login_endpoint(
    login_in: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate athlete with email and password."""
    athlete, token = await authenticate_user(db, login_in)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        athlete=AthleteRead.model_validate(athlete),
    )


@router.get("/me", response_model=AthleteRead)
async def get_me_endpoint(
    current_athlete: Athlete = Depends(get_current_athlete),
):
    """Return the profile of the currently authenticated athlete."""
    return AthleteRead.model_validate(current_athlete)
