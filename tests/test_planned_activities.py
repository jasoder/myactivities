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
async def test_planned_activity_create_mocked():
    """Test planned activity creation with mocked service."""
    async with mock_app() as client:
        with patch("app.services.planned_activity_service.create_planned_activity") as mock_create:
            activity_id, athlete_id = uuid.uuid4(), uuid.uuid4()
            mock_create.return_value = mock_obj(
                id=activity_id,
                athlete_id=athlete_id,
                name="Test",
                type="Ride",
                goal=None,
                zone=None,
                target_duration=None,
                target_distance=None,
                target_intensity=None,
                scheduled_date=datetime.now(timezone.utc),
                completed=False,
                linked_activity_id=None,
                created_at=datetime.now(timezone.utc),
            )

            payload = {
                "athlete_id": str(athlete_id), "name": "Test", "type": "Ride",
                "scheduled_date": datetime.now(timezone.utc).isoformat()
            }
            r = await client.post("/myactivities/plannedworkouts/", json=payload)
            assert r.status_code == 201


@pytest.mark.asyncio
async def test_planned_activity_get_by_athlete_mocked():
    """Test getting planned activities by athlete."""
    async with mock_app() as client:
        athlete_id, activity_id = uuid.uuid4(), uuid.uuid4()
        with patch("app.services.planned_activity_service.get_planned_activities_by_athlete") as mock_get:
            mock_get.return_value = [
                mock_obj(
                    id=activity_id,
                    athlete_id=athlete_id,
                    name="Test",
                    type="Ride",
                    goal=None,
                    zone=None,
                    target_duration=None,
                    target_distance=None,
                    target_intensity=None,
                    scheduled_date=datetime.now(timezone.utc),
                    completed=False,
                    linked_activity_id=None,
                    created_at=datetime.now(timezone.utc),
                )
            ]

            r = await client.get(f"/myactivities/plannedworkouts/athlete/{athlete_id}")
            assert r.status_code == 200


@pytest.mark.asyncio
async def test_planned_activity_update_mocked():
    """Test planned activity update."""
    async with mock_app() as client:
        activity_id = uuid.uuid4()
        with patch("app.services.planned_activity_service.get_planned_activity_by_id") as mock_get, \
             patch("app.services.planned_activity_service.update_planned_activity") as mock_update:
            mock_activity = mock_obj(
                id=activity_id,
                athlete_id=uuid.uuid4(),
                name="Updated",
                type="Ride",
                goal=None,
                zone=None,
                target_duration=None,
                target_distance=None,
                target_intensity=None,
                scheduled_date=datetime.now(timezone.utc),
                completed=False,
                linked_activity_id=None,
                created_at=datetime.now(timezone.utc),
            )
            mock_get.return_value = mock_activity
            mock_update.return_value = mock_activity

            r = await client.put(f"/myactivities/plannedworkouts/{activity_id}", json={"name": "Updated"})
            assert r.status_code == 200


@pytest.mark.asyncio
async def test_planned_activity_delete_mocked():
    """Test planned activity deletion."""
    async with mock_app() as client:
        activity_id = uuid.uuid4()
        with patch("app.services.planned_activity_service.get_planned_activity_by_id") as mock_get, \
             patch("app.services.planned_activity_service.delete_planned_activity") as mock_delete:
            mock_get.return_value = mock_obj(
                id=activity_id,
            )
            mock_delete.return_value = None

            r = await client.delete(f"/myactivities/plannedworkouts/{activity_id}")
            assert r.status_code == 204
