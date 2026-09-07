import pytest
import sys
from pathlib import Path
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from contextlib import asynccontextmanager
from urllib.parse import quote

# Ensure src is on path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from app.main import app
from app.db.session import get_db

athlete_id = uuid.uuid4()
week_start = datetime(2026, 1, 5, 0, 0, 0, tzinfo=timezone.utc)


@asynccontextmanager
async def mock_app():
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
    obj = MagicMock()
    for k, v in kwargs.items():
        setattr(obj, k, v)
    return obj


@pytest.mark.asyncio
async def test_strava_webhook_challenge():
    """Test Strava GET webhook verification."""
    async with mock_app() as client:
        with patch.dict("os.environ", {"STRAVA_VERIFY_TOKEN": "secret_token"}):
            res = await client.get(
                "/myactivities/strava/webhook?hub.mode=subscribe&hub.challenge=test_challenge&hub.verify_token=secret_token"
            )
            assert res.status_code == 200
            assert res.json() == {"hub.challenge": "test_challenge"}


@pytest.mark.asyncio
async def test_strava_webhook_event_trigger():
    """Test Strava POST webhook activity event dispatch."""
    async with mock_app() as client:
        with patch("app.services.strava_sync_service.sync_athlete_activities", new_callable=AsyncMock) as mock_sync:
            payload = {
                "object_type": "athlete",
                "object_id": 12345,
                "aspect_type": "update",
                "owner_id": 99999,
                "event_time": 1700000000,
            }
            res = await client.post("/myactivities/strava/webhook", json=payload)
            assert res.status_code == 200
            assert res.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_ai_generate_week_plan_preview():
    """Test AI adaptive scheduling plan generation endpoint."""
    async with mock_app() as client:
        with patch("app.api.routers.ai.generate_adaptive_week_plan", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = {
                "athlete_id": str(athlete_id),
                "week_start_date": week_start.isoformat(),
                "reasoning": "Aerobic base focus",
                "workouts": [
                    {
                        "day_offset": 0,
                        "planned_date": week_start.isoformat(),
                        "name": "Base Ride",
                        "sport_type": "Ride",
                        "duration_min": 60,
                        "distance_m": 20000.0,
                        "intensity": 70.0,
                        "plan_metadata": {"reasoning": "Easy zone 2"},
                    }
                ],
            }

            url = f"/myactivities/ai/generate-week-plan?athlete_id={athlete_id}&week_start={quote(week_start.isoformat())}"
            res = await client.post(url)
            assert res.status_code == 200
            data = res.json()
            assert "workouts" in data
            assert len(data["workouts"]) == 1
            assert data["workouts"][0]["name"] == "Base Ride"


@pytest.mark.asyncio
async def test_ai_confirm_week_plan():
    """Test AI adaptive scheduling plan confirmation."""
    async with mock_app() as client:
        with patch("app.api.routers.ai.confirm_adaptive_week_plan", new_callable=AsyncMock) as mock_confirm:
            wp_id = uuid.uuid4()
            mock_wp = mock_obj(id=wp_id, status="confirmed")
            mock_confirm.return_value = mock_wp

            payload = {
                "athlete_id": str(athlete_id),
                "week_start_date": week_start.isoformat(),
                "reasoning": "Aerobic base focus",
                "workouts": [
                    {
                        "day_offset": 0,
                        "planned_date": week_start.isoformat(),
                        "name": "Base Ride",
                        "sport_type": "Ride",
                        "duration_min": 60,
                    }
                ],
            }

            res = await client.post("/myactivities/ai/confirm-week-plan", json=payload)
            assert res.status_code == 201
            assert res.json()["week_plan_id"] == str(wp_id)
            assert res.json()["status"] == "confirmed"


@pytest.mark.asyncio
async def test_ai_weekly_recap():
    """Test AI weekly recap / morning report."""
    async with mock_app() as client:
        with patch("app.api.routers.ai.generate_weekly_recap", new_callable=AsyncMock) as mock_recap:
            mock_recap.return_value = {
                "athlete_id": str(athlete_id),
                "week_start": week_start.isoformat(),
                "planned_sessions": 5,
                "completed_sessions": 5,
                "compliance_rate": 100.0,
                "total_completed_hours": 6.5,
                "summary": "Completed 5 sessions totaling 6.5 hours.",
            }

            url = f"/myactivities/ai/weekly-recap/{athlete_id}?week_start={quote(week_start.isoformat())}"
            res = await client.get(url)
            assert res.status_code == 200
            assert res.json()["compliance_rate"] == 100.0
