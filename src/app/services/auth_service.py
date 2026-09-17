import uuid
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.athlete import Athlete
from app.schemas.auth import RegisterRequest, LoginRequest
from app.core.security import (
    hash_password,
    verify_password,
    dummy_verify_password,
    create_access_token,
    decode_access_token,
)

security_bearer = HTTPBearer(auto_error=False)


async def register_user(db: AsyncSession, register_data: RegisterRequest) -> tuple[Athlete, str]:
    """Register a new user with email and password following OWASP guidelines."""
    normalized_email = register_data.email.strip().lower()

    # Check if email is already in use
    existing = await db.execute(select(Athlete).where(Athlete.email == normalized_email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    # Hash password with Argon2id
    hashed = hash_password(register_data.password)

    athlete = Athlete(
        email=normalized_email,
        name=register_data.name,
        hashed_password=hashed,
    )
    db.add(athlete)
    await db.commit()
    await db.refresh(athlete)

    # Issue JWT token
    token = create_access_token({"sub": str(athlete.id), "email": athlete.email})
    return athlete, token


async def authenticate_user(db: AsyncSession, login_data: LoginRequest) -> tuple[Athlete, str]:
    """Authenticate a user with email and password with constant-time failure response."""
    normalized_email = login_data.email.strip().lower()

    # Find athlete
    result = await db.execute(select(Athlete).where(Athlete.email == normalized_email))
    athlete = result.scalar_one_or_none()

    generic_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not athlete or not athlete.hashed_password:
        # Run dummy verification to prevent timing attack enumeration
        dummy_verify_password(login_data.password)
        raise generic_error

    if not verify_password(login_data.password, athlete.hashed_password):
        raise generic_error

    token = create_access_token({"sub": str(athlete.id), "email": athlete.email})
    return athlete, token


async def get_current_athlete(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: AsyncSession = Depends(get_db),
) -> Athlete:
    """FastAPI dependency to extract and validate the authenticated athlete from the Bearer token."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    athlete_id_str = payload.get("sub")
    if not athlete_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject identifier.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        athlete_id = uuid.UUID(athlete_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed subject identifier in token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(Athlete).where(Athlete.id == athlete_id))
    athlete = result.scalar_one_or_none()
    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Athlete account not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return athlete
