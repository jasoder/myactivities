from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.athlete import Athlete
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.schemas.athlete import AthleteRead
from app.core.security import ACCESS_TOKEN_EXPIRE_SECONDS
from app.services.auth_service import (
    register_user,
    authenticate_user,
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
        expires_in=ACCESS_TOKEN_EXPIRE_SECONDS,
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
        expires_in=ACCESS_TOKEN_EXPIRE_SECONDS,
        athlete=AthleteRead.model_validate(athlete),
    )
