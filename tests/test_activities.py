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
from app.models.activities import Activity, ActivityMetric, ActivityStatus
from app.enums import ActivitySource

athlete_id = uuid.uuid4()
today = datetime(2026, 1, 6, 12, 0, 0, tzinfo=timezone.utc)
tomorrow = datetime(2026, 1, 7, 12, 0, 0, tzinfo=timezone.utc)
yesterday = datetime(2026, 1, 5, 12, 0, 0, tzinfo=timezone.utc)


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
async def test_get_activities_for_athlete_with_activities():
    """Test retrieving activities for an athlete with both completed and planned activities."""
    async with mock_app() as client:
        mock_activities = [
            mock_obj(
                id=uuid.uuid4(),
                athlete_id=athlete_id,
                name="Morning Ride",
                source=ActivitySource.STRAVA,
                status=ActivityStatus.completed,
                sport_type="Ride",
                planned_date=None,
                actual_date=today,
                distance_m=30000.0,
                duration_min=60,
                intensity=None,
                metrics=mock_obj(
                    distance_m=30000.0,
                    duration_min=60,
                    icu_training_load=85.5,
                ),
            ),
            mock_obj(
                id=uuid.uuid4(),
                athlete_id=athlete_id,
                name="Evening Run",
                source=ActivitySource.manual,
                status=ActivityStatus.planned,
                sport_type="Run",
                planned_date=tomorrow,
                actual_date=None,
                distance_m=10000.0,
                duration_min=45,
                intensity=None,
                metrics=None,
            ),
        ]

        with patch("app.services.activities_service.get_activities_by_date_range") as mock_get:
            mock_get.return_value = mock_activities

            start_date_str = quote(yesterday.isoformat())
            end_date_str = quote((tomorrow + timedelta(days=1)).isoformat())

            response = await client.get(
                f"/myactivities/activities/{athlete_id}?start_date={start_date_str}&end_date={end_date_str}"
            )

            assert response.status_code == 200
            data = response.json()
            assert "events" in data
            assert len(data["events"]) == 2

            assert data["events"][0]["title"] == "Morning Ride"
            assert datetime.fromisoformat(data["events"][0]["date"]) == today
            assert data["events"][0]["type"] == "Ride"
            assert data["events"][0]["status"] == "completed"

            assert data["events"][1]["title"] == "Evening Run"
            assert datetime.fromisoformat(data["events"][1]["date"]) == tomorrow
            assert data["events"][1]["type"] == "Run"
            assert data["events"][1]["status"] == "planned"


@pytest.mark.asyncio
async def test_get_activities_for_athlete_no_activities_in_range():
    """Test retrieving activities for an athlete with no activities within the date range."""
    async with mock_app() as client:
        test_athlete_id = uuid.uuid4()
        start_date = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2026, 1, 7, tzinfo=timezone.utc)

        with patch("app.services.activities_service.get_activities_by_date_range") as mock_get:
            mock_get.return_value = []

            response = await client.get(
                f"/myactivities/activities/{test_athlete_id}?start_date={quote(start_date.isoformat())}&end_date={quote(end_date.isoformat())}"
            )

            assert response.status_code == 200
            data = response.json()
            assert "events" in data
            assert len(data["events"]) == 0


@pytest.mark.asyncio
async def test_get_activities_with_invalid_date_format():
    """Test retrieving activities with invalid date formats."""
    async with mock_app() as client:
        test_athlete_id = uuid.uuid4()
        invalid_start_date = "2026-13-01T00:00:00Z"
        valid_end_date = quote(datetime(2026, 1, 7, tzinfo=timezone.utc).isoformat())

        response = await client.get(
            f"/myactivities/activities/{test_athlete_id}?start_date={invalid_start_date}&end_date={valid_end_date}"
        )
        assert response.status_code == 422
        assert "detail" in response.json()

        valid_start_date = quote(datetime(2026, 1, 1, tzinfo=timezone.utc).isoformat())
        invalid_end_date = "not-a-date"

        response = await client.get(
            f"/myactivities/activities/{test_athlete_id}?start_date={valid_start_date}&end_date={invalid_end_date}"
        )
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_activities_ordering():
    """Test that activity events are returned in chronological order."""
    async with mock_app() as client:
        test_athlete_id = uuid.uuid4()
        today_event = datetime(2026, 1, 6, 12, 0, 0, tzinfo=timezone.utc)
        day_plus_1_event = datetime(2026, 1, 7, 12, 0, 0, tzinfo=timezone.utc)
        day_plus_2_event = datetime(2026, 1, 8, 12, 0, 0, tzinfo=timezone.utc)

        mock_activities = [
            mock_obj(
                id=uuid.uuid4(),
                athlete_id=test_athlete_id,
                name="Start Activity",
                source=ActivitySource.manual,
                status=ActivityStatus.planned,
                sport_type="Ride",
                planned_date=today_event,
                actual_date=None,
                distance_m=20000.0,
                duration_min=60,
                intensity=None,
                metrics=None,
            ),
            mock_obj(
                id=uuid.uuid4(),
                athlete_id=test_athlete_id,
                name="Middle Activity",
                source=ActivitySource.STRAVA,
                status=ActivityStatus.completed,
                sport_type="Run",
                planned_date=None,
                actual_date=day_plus_1_event,
                distance_m=5000.0,
                duration_min=30,
                intensity=None,
                metrics=mock_obj(distance_m=5000.0, duration_min=30, icu_training_load=None),
            ),
            mock_obj(
                id=uuid.uuid4(),
                athlete_id=test_athlete_id,
                name="End Activity",
                source=ActivitySource.STRAVA,
                status=ActivityStatus.completed,
                sport_type="Swim",
                planned_date=None,
                actual_date=day_plus_2_event,
                distance_m=1000.0,
                duration_min=20,
                intensity=None,
                metrics=mock_obj(distance_m=1000.0, duration_min=20, icu_training_load=None),
            ),
        ]

        with patch("app.services.activities_service.get_activities_by_date_range") as mock_get:
            mock_get.return_value = mock_activities
            start_date_str = quote(yesterday.isoformat())
            end_date_str = quote((day_plus_2_event + timedelta(days=1)).isoformat())

            response = await client.get(
                f"/myactivities/activities/{test_athlete_id}?start_date={start_date_str}&end_date={end_date_str}"
            )

            assert response.status_code == 200
            data = response.json()
            assert "events" in data
            assert len(data["events"]) == 3

            assert data["events"][0]["title"] == "Start Activity"
            assert datetime.fromisoformat(data["events"][0]["date"]) == today_event
            assert data["events"][1]["title"] == "Middle Activity"
            assert datetime.fromisoformat(data["events"][1]["date"]) == day_plus_1_event
            assert data["events"][2]["title"] == "End Activity"
            assert datetime.fromisoformat(data["events"][2]["date"]) == day_plus_2_event


@pytest.mark.asyncio
async def test_get_activities_missing_start_date():
    """Test retrieving activities with a missing start_date query parameter."""
    async with mock_app() as client:
        test_athlete_id = uuid.uuid4()
        end_date = quote(datetime(2026, 1, 7, tzinfo=timezone.utc).isoformat())

        response = await client.get(
            f"/myactivities/activities/{test_athlete_id}?end_date={end_date}"
        )
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_activities_missing_end_date():
    """Test retrieving activities with a missing end_date query parameter."""
    async with mock_app() as client:
        test_athlete_id = uuid.uuid4()
        start_date = quote(datetime(2026, 1, 1, tzinfo=timezone.utc).isoformat())

        response = await client.get(
            f"/myactivities/activities/{test_athlete_id}?start_date={start_date}"
        )
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_and_get_activity_crud():
    """Test creating and retrieving an activity via unified endpoints."""
    async with mock_app() as client:
        act_id = uuid.uuid4()
        with patch("app.services.activities_service.create_activity") as mock_create, \
             patch("app.services.activities_service.get_activity_by_id") as mock_get:
            
            mock_act = mock_obj(
                id=act_id,
                athlete_id=athlete_id,
                source=ActivitySource.manual,
                status=ActivityStatus.planned,
                sport_type="Run",
                planned_date=tomorrow,
                actual_date=None,
                name="Tempo Run",
                description="Threshold intervals",
                duration_min=45,
                distance_m=8000.0,
                intensity=80.0,
                week_plan_id=None,
                matched_strava_activity_id=None,
                reconciliation_note=None,
                plan_metadata=None,
                created_at=datetime.now(timezone.utc),
                updated_at=None,
                metrics=None,
            )
            mock_create.return_value = mock_act
            mock_get.return_value = mock_act

            payload = {
                "athlete_id": str(athlete_id),
                "source": "manual",
                "status": "planned",
                "sport_type": "Run",
                "planned_date": tomorrow.isoformat(),
                "name": "Tempo Run",
                "duration_min": 45,
                "distance_m": 8000.0,
            }

            create_res = await client.post("/myactivities/activities/", json=payload)
            assert create_res.status_code == 201
            assert create_res.json()["name"] == "Tempo Run"

            detail_res = await client.get(f"/myactivities/activities/detail/{act_id}")
            assert detail_res.status_code == 200
            assert detail_res.json()["name"] == "Tempo Run"