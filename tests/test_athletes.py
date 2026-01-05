import pytest
import sys
from pathlib import Path
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from contextlib import asynccontextmanager

# Ensure src is on path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from app.main import app
from app.db.session import get_db


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


def mock_obj(**kwargs):
    """Create a MagicMock with given attributes."""
    obj = MagicMock()
    for k, v in kwargs.items():
        setattr(obj, k, v)
    return obj


@pytest.mark.asyncio
async def test_athlete_create_mocked():
    """Test athlete creation with mocked service."""
    async with mock_app() as client:
        with patch("app.services.athlete_service.create_new_athlete") as mock_create:
            test_id = uuid.uuid4()
            mock_create.return_value = mock_obj(id=test_id, email="test@example.com")

            r = await client.post("/myactivities/athletes/", json={"email": "test@example.com", "name": "Test"})
            assert r.status_code == 201


@pytest.mark.asyncio
async def test_athlete_get_mocked():
    """Test athlete retrieval with mocked service."""
    async with mock_app() as client:
        test_id = uuid.uuid4()
        with patch("app.services.athlete_service.get_athlete_by_id") as mock_get:
            mock_get.return_value = mock_obj(
                id=test_id, email="test@example.com", name="Test",
                ftp=None, threshold_pace=None, weight=None, max_hr=None, lthr=None,
                strava_id=None, intervals_icu_id=None, access_token=None, refresh_token=None,
                token_expires_at=None, preferred_sports=None, timezone="UTC", weekly_training_hours=None,
                ai_enabled=True, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
            )

            r = await client.get(f"/myactivities/athletes/{test_id}")
            assert r.status_code == 200


@pytest.mark.asyncio
async def test_athlete_get_not_found_mocked():
    """Test 404 when athlete doesn't exist."""
    async with mock_app() as client:
        with patch("app.services.athlete_service.get_athlete_by_id") as mock_get:
            mock_get.return_value = None
            r = await client.get(f"/myactivities/athletes/{uuid.uuid4()}")
            assert r.status_code == 404
