import pytest
import sys
from pathlib import Path
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from contextlib import asynccontextmanager

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from app.main import app
from app.db.session import get_db
from app.core.security import (
    hash_password,
    verify_password,
    dummy_verify_password,
    create_access_token,
    decode_access_token,
)
from app.models.athlete import Athlete


@asynccontextmanager
async def mock_app():
    """Async context manager that provides a test client with mocked DB."""
    mock_db = AsyncMock()

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client
    finally:
        app.dependency_overrides.clear()


def make_mock_athlete(athlete_id=None, email="user@example.com", name="Test User", hashed_pwd=None):
    athlete = MagicMock(spec=Athlete)
    athlete.id = athlete_id or uuid.uuid4()
    athlete.email = email
    athlete.name = name
    athlete.hashed_password = hashed_pwd
    athlete.ftp = None
    athlete.threshold_pace = None
    athlete.weight = None
    athlete.max_hr = None
    athlete.lthr = None
    athlete.strava_id = None
    athlete.access_token = None
    athlete.refresh_token = None
    athlete.token_expires_at = None
    athlete.preferred_sports = []
    athlete.timezone = "UTC"
    athlete.weekly_training_hours = None
    athlete.ai_enabled = True
    athlete.created_at = datetime.now(timezone.utc)
    athlete.updated_at = datetime.now(timezone.utc)
    return athlete


# 1. Security Unit Tests
def test_argon2_hashing_and_verification():
    raw = "MySecurePassword123!"
    hashed = hash_password(raw)
    assert hashed != raw
    assert hashed.startswith("$argon2")
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_dummy_verify_password():
    assert dummy_verify_password("some_random_password") is False


def test_jwt_create_and_decode():
    sub = str(uuid.uuid4())
    token = create_access_token({"sub": sub, "email": "test@example.com"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == sub
    assert payload["email"] == "test@example.com"
    assert "exp" in payload


def test_jwt_decode_invalid():
    assert decode_access_token("invalid.token.here") is None


# 2. Auth Endpoint Tests
@pytest.mark.asyncio
async def test_register_success():
    async with mock_app() as client:
        with patch("app.api.routers.auth.register_user", new_callable=AsyncMock) as mock_reg:
            test_id = uuid.uuid4()
            mock_athlete = make_mock_athlete(athlete_id=test_id, email="runner@example.com")
            mock_reg.return_value = (mock_athlete, "mock_jwt_token")

            res = await client.post(
                "/myactivities/auth/register",
                json={"email": "runner@example.com", "password": "Password123!", "name": "Runner"},
            )
            assert res.status_code == 201
            data = res.json()
            assert data["access_token"] == "mock_jwt_token"
            assert data["token_type"] == "bearer"
            assert data["expires_in"] > 0
            assert data["athlete"]["email"] == "runner@example.com"
            assert "access_token" not in data["athlete"]
            assert "refresh_token" not in data["athlete"]
            assert "hashed_password" not in data["athlete"]
            assert "strava_connected" in data["athlete"]


@pytest.mark.asyncio
async def test_register_password_too_short():
    async with mock_app() as client:
        res = await client.post(
            "/myactivities/auth/register",
            json={"email": "runner@example.com", "password": "short"},
        )
        assert res.status_code == 422


@pytest.mark.asyncio
async def test_login_success():
    async with mock_app() as client:
        with patch("app.api.routers.auth.authenticate_user", new_callable=AsyncMock) as mock_auth:
            test_id = uuid.uuid4()
            mock_athlete = make_mock_athlete(athlete_id=test_id, email="runner@example.com")
            mock_auth.return_value = (mock_athlete, "valid_token_xyz")

            res = await client.post(
                "/myactivities/auth/login",
                json={"email": "runner@example.com", "password": "Password123!"},
            )
            assert res.status_code == 200
            data = res.json()
            assert data["access_token"] == "valid_token_xyz"
            assert data["token_type"] == "bearer"
            assert data["expires_in"] > 0
            assert data["athlete"]["email"] == "runner@example.com"
            assert "access_token" not in data["athlete"]
            assert "refresh_token" not in data["athlete"]
            assert "hashed_password" not in data["athlete"]


@pytest.mark.asyncio
async def test_get_me_without_token():
    async with mock_app() as client:
        res = await client.get("/myactivities/user")
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_valid_token():
    from app.services.auth_service import get_current_athlete

    test_id = uuid.uuid4()
    mock_athlete = make_mock_athlete(athlete_id=test_id, email="athlete@example.com")

    async def mock_get_current_athlete():
        return mock_athlete

    async with mock_app() as client:
        app.dependency_overrides[get_current_athlete] = mock_get_current_athlete
        try:
            res = await client.get(
                "/myactivities/user",
                headers={"Authorization": "Bearer mock_token"},
            )
            assert res.status_code == 200
            assert res.json()["email"] == "athlete@example.com"
        finally:
            app.dependency_overrides.pop(get_current_athlete, None)



@pytest.mark.asyncio
async def test_get_current_athlete_real_token_variations():
    from app.services.auth_service import get_current_athlete
    from fastapi.security import HTTPAuthorizationCredentials

    test_id = uuid.uuid4()
    token = create_access_token({"sub": str(test_id), "email": "athlete@example.com"})
    mock_athlete = make_mock_athlete(athlete_id=test_id, email="athlete@example.com")

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_athlete
    mock_db.execute.return_value = mock_result

    # 1. Normal clean token
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    user = await get_current_athlete(creds, mock_db)
    assert user.id == test_id

    # 2. Token with accidental redundant 'Bearer ' prefix (from Swagger UI paste)
    creds_double = HTTPAuthorizationCredentials(scheme="Bearer", credentials=f"Bearer {token}")
    user_double = await get_current_athlete(creds_double, mock_db)
    assert user_double.id == test_id

    # 3. Token with surrounding quotes (from JSON copy paste)
    creds_quotes = HTTPAuthorizationCredentials(scheme="Bearer", credentials=f'"{token}"')
    user_quotes = await get_current_athlete(creds_quotes, mock_db)
    assert user_quotes.id == test_id


# 3. Service Level Auth Tests
@pytest.mark.asyncio
async def test_service_register_duplicate_email():
    from app.services.auth_service import register_user
    from app.schemas.auth import RegisterRequest
    from fastapi import HTTPException

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = make_mock_athlete()
    mock_db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await register_user(mock_db, RegisterRequest(email="dup@example.com", password="Password123!"))
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_service_authenticate_bad_password():
    from app.services.auth_service import authenticate_user
    from app.schemas.auth import LoginRequest
    from fastapi import HTTPException

    mock_db = AsyncMock()
    mock_result = MagicMock()
    hashed = hash_password("CorrectPassword123!")
    mock_result.scalar_one_or_none.return_value = make_mock_athlete(hashed_pwd=hashed)
    mock_db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await authenticate_user(mock_db, LoginRequest(email="user@example.com", password="WrongPassword!"))
    assert exc_info.value.status_code == 401
    assert "Invalid email or password" in exc_info.value.detail


@pytest.mark.asyncio
async def test_service_authenticate_nonexistent_user_calls_dummy():
    from app.services.auth_service import authenticate_user
    from app.schemas.auth import LoginRequest
    from fastapi import HTTPException

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    with patch("app.services.auth_service.dummy_verify_password") as mock_dummy:
        with pytest.raises(HTTPException) as exc_info:
            await authenticate_user(mock_db, LoginRequest(email="unknown@example.com", password="Password123!"))
        assert exc_info.value.status_code == 401
        assert mock_dummy.called

