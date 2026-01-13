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
from app.models.athlete import Athlete
from app.models.completed_activity import CompletedActivity
from app.models.planned_activity import PlannedActivity
from app.enums import ActivityType, ActivityGoal, ActivitySource

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
    """Test retrieving a activities for an athlete with both completed and planned activities."""
    async with mock_app() as client:

        mock_planned = [
            mock_obj(
                id=uuid.uuid4(),
                athlete_id=athlete_id,
                name="Evening Run",
                type=ActivityType.run,
                goal=ActivityGoal.endurance,
                zone=None,
                target_duration=2700,
                target_distance=10000.0,
                target_intensity=None,
                scheduled_date=tomorrow,
                completed=False,
                linked_activity_id=None,
                created_at=datetime.now(timezone.utc),
            )
        ]
        mock_completed = [
            mock_obj(
                id=uuid.uuid4(),
                athlete_id=athlete_id,
                name="Morning Ride",
                source=ActivitySource.STRAVA,
                external_id=None,
                strava_id=None,
                intervals_id=None,
                sport_type="Ride",
                sub_type=None,
                start_date=today,
                start_date_local=today,
                timezone=None,
                trainer=False,
                commute=False,
                race=False,
                distance_m=30000.0,
                elapsed_time_s=3600,
                moving_time_s=3600,
                elevation_gain_m=None,
                elevation_loss_m=None,
                average_speed_mps=None,
                max_speed_mps=None,
                average_cadence=None,
                average_temp_c=None,
                max_temp_c=None,
                min_temp_c=None,
                average_hr_bpm=None,
                max_hr_bpm=None,
                average_power_w=None,
                weighted_power_w=None,
                max_power_w=None,
                calories_kcal=None,
                carbs_used_g=None,
                icu_training_load=85.5,
                icu_trimp=None,
                icu_intensity=None,
                icu_efficiency_factor=None,
                icu_variability_index=None,
                icu_joules=None,
                icu_rpe=None,
                device_name=None,
                gear_id=None,
                gear_name=None,
                gear_distance_m=None,
                created_at=datetime.now(timezone.utc),
                updated_at=None,
                last_sync=None,
                icu_sync_date=None,
                strava_sync_date=None,
                analyzed=False,
                strava_url=None,
                intervals_url=None,
            )
        ]

        with (
            patch("app.services.planned_activity_service.get_planned_activities_by_date_range") as mock_get_planned,
            patch("app.services.completed_activity_service.get_completed_activities_by_date_range") as mock_get_completed,
        ):

            mock_get_planned.return_value = mock_planned
            mock_get_completed.return_value = mock_completed

            # Fix: Ensure timezone information is kept when converting to string AND format is compatible
            # Use isoformat directly, Pydantic should handle the default ISO format including microseconds
            start_date_str = quote(yesterday.isoformat())
            end_date_str = quote((tomorrow + timedelta(days=1)).isoformat()) # Range covers yesterday, today and tomorrow

            response = await client.get(
                f"/myactivities/activities/{athlete_id}?start_date={start_date_str}&end_date={end_date_str}"
            )

            assert response.status_code == 200
            data = response.json()
            assert "events" in data
            assert len(data["events"]) == 2 # Only activities within the range, sorted

            # Check for correct data and order (sorted by date, completed then planned for same date)
            assert data["events"][0]["title"] == mock_completed[0].name
            assert datetime.fromisoformat(data["events"][0]["date"]) == mock_completed[0].start_date_local
            assert data["events"][0]["type"] == mock_completed[0].sport_type
            assert data["events"][0]["status"] == "completed"

            assert data["events"][1]["title"] == mock_planned[0].name
            assert datetime.fromisoformat(data["events"][1]["date"]) == mock_planned[0].scheduled_date
            assert data["events"][1]["type"] == mock_planned[0].type
            assert data["events"][1]["status"] == "planned"


@pytest.mark.asyncio
async def test_get_activities_for_athlete_no_activities_in_range():
    """Test retrieving a activities for an athlete with no activities within the specified date range."""
    async with mock_app() as client:
        athlete_id = uuid.uuid4()
        start_date = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2026, 1, 7, tzinfo=timezone.utc)

        with (
            patch("app.services.planned_activity_service.get_planned_activities_by_date_range") as mock_get_planned,
            patch("app.services.completed_activity_service.get_completed_activities_by_date_range") as mock_get_completed,
        ):

            mock_get_planned.return_value = []
            mock_get_completed.return_value = []

            response = await client.get(
                f"/myactivities/activities/{athlete_id}?start_date={quote(start_date.isoformat())}&end_date={quote(end_date.isoformat())}"
            )

            assert response.status_code == 200
            data = response.json()
            assert "events" in data
            assert len(data["events"]) == 0

@pytest.mark.asyncio
async def test_get_activities_with_invalid_date_format():
    """Test retrieving a activities with invalid date formats."""
    async with mock_app() as client:
        athlete_id = uuid.uuid4()
        invalid_start_date = "2026-13-01T00:00:00Z" # Invalid month
        valid_end_date = quote(datetime(2026, 1, 7, tzinfo=timezone.utc).isoformat())

        response = await client.get(
            f"/myactivities/activities/{athlete_id}?start_date={invalid_start_date}&end_date={valid_end_date}"
        )
        assert response.status_code == 422 # Unprocessable Entity for Pydantic validation error
        assert "detail" in response.json()
        assert "month value is outside expected range of 1-12" in response.json()["detail"][0]["msg"]

        valid_start_date = quote(datetime(2026, 1, 1, tzinfo=timezone.utc).isoformat())
        invalid_end_date = "not-a-date" # Completely invalid

        response = await client.get(
            f"/myactivities/activities/{athlete_id}?start_date={valid_start_date}&end_date={invalid_end_date}"
        )
        assert response.status_code == 422
        assert "detail" in response.json()
        assert "valid datetime" in response.json()["detail"][0]["msg"].lower()

@pytest.mark.asyncio
async def test_get_activities_with_end_date_before_start_date():
    """Test retrieving a activities when end_date is before start_date."""
    async with mock_app() as client:
        athlete_id = uuid.uuid4()
        start_date = datetime(2026, 1, 7, tzinfo=timezone.utc)
        end_date = datetime(2026, 1, 1, tzinfo=timezone.utc)

        with (
            patch("app.services.planned_activity_service.get_planned_activities_by_date_range") as mock_get_planned,
            patch("app.services.completed_activity_service.get_completed_activities_by_date_range") as mock_get_completed,
        ):

            mock_get_planned.return_value = []
            mock_get_completed.return_value = []

            # The service logic might handle this gracefully and return empty list, 
            # or the validation could be added at the API level (FastAPI will enforce Query params, not their logical order)
            response = await client.get(
                f"/myactivities/activities/{athlete_id}?start_date={quote(start_date.isoformat())}&end_date={quote(end_date.isoformat())}"
            )
            assert response.status_code == 200
            data = response.json()
            assert "events" in data
            assert len(data["events"]) == 0

@pytest.mark.asyncio
async def test_get_activities_ordering():
    """Test that activities events are returned in chronological order."""
    async with mock_app() as client:
        athlete_id = uuid.uuid4()
        today_event = datetime(2026, 1, 6, 12, 0, 0, tzinfo=timezone.utc)
        day_plus_1_event = datetime(2026, 1, 7, 12, 0, 0, tzinfo=timezone.utc)
        day_plus_2_event = datetime(2026, 1, 8, 12, 0, 0, tzinfo=timezone.utc)

        mock_planned = [
            mock_obj(
                id=uuid.uuid4(),
                athlete_id=athlete_id,
                name="Start Activity",
                type=ActivityType.ride,
                goal=ActivityGoal.endurance,
                zone=None,
                target_duration=3600,
                target_distance=20000.0,
                target_intensity=None,
                scheduled_date=today_event,
                completed=False,
                linked_activity_id=None,
                created_at=datetime.now(timezone.utc),
            )
        ]
        mock_completed = [
            mock_obj(
                id=uuid.uuid4(),
                athlete_id=athlete_id,
                name="Middle Activity",
                source=ActivitySource.STRAVA,
                external_id=None,
                strava_id=None,
                intervals_id=None,
                sport_type="Run",
                sub_type=None,
                start_date=day_plus_1_event,
                start_date_local=day_plus_1_event,
                timezone=None,
                trainer=False,
                commute=False,
                race=False,
                distance_m=5000.0,
                elapsed_time_s=1800,
                moving_time_s=1800,
                elevation_gain_m=None,
                elevation_loss_m=None,
                average_speed_mps=None,
                max_speed_mps=None,
                average_cadence=None,
                average_temp_c=None,
                max_temp_c=None,
                min_temp_c=None,
                average_hr_bpm=None,
                max_hr_bpm=None,
                average_power_w=None,
                weighted_power_w=None,
                max_power_w=None,
                calories_kcal=None,
                carbs_used_g=None,
                icu_training_load=None,
                icu_trimp=None,
                icu_intensity=None,
                icu_efficiency_factor=None,
                icu_variability_index=None,
                icu_joules=None,
                icu_rpe=None,
                device_name=None,
                gear_id=None,
                gear_name=None,
                gear_distance_m=None,
                created_at=datetime.now(timezone.utc),
                updated_at=None,
                last_sync=None,
                icu_sync_date=None,
                strava_sync_date=None,
                analyzed=False,
                strava_url=None,
                intervals_url=None,
            ),
            mock_obj(
                id=uuid.uuid4(),
                athlete_id=athlete_id,
                name="End Activity",
                source=ActivitySource.STRAVA,
                external_id=None,
                strava_id=None,
                intervals_id=None,
                sport_type="Swim",
                sub_type=None,
                start_date=day_plus_2_event,
                start_date_local=day_plus_2_event,
                timezone=None,
                trainer=False,
                commute=False,
                race=False,
                distance_m=1000.0,
                elapsed_time_s=1200,
                moving_time_s=1200,
                elevation_gain_m=None,
                elevation_loss_m=None,
                average_speed_mps=None,
                max_speed_mps=None,
                average_cadence=None,
                average_temp_c=None,
                max_temp_c=None,
                min_temp_c=None,
                average_hr_bpm=None,
                max_hr_bpm=None,
                average_power_w=None,
                weighted_power_w=None,
                max_power_w=None,
                calories_kcal=None,
                carbs_used_g=None,
                icu_training_load=None,
                icu_trimp=None,
                icu_intensity=None,
                icu_efficiency_factor=None,
                icu_variability_index=None,
                icu_joules=None,
                icu_rpe=None,
                device_name=None,
                gear_id=None,
                gear_name=None,
                gear_distance_m=None,
                created_at=datetime.now(timezone.utc),
                updated_at=None,
                last_sync=None,
                icu_sync_date=None,
                strava_sync_date=None,
                analyzed=False,
                strava_url=None,
                intervals_url=None,
            )
        ]

        with (
            patch("app.services.planned_activity_service.get_planned_activities_by_date_range") as mock_get_planned,
            patch("app.services.completed_activity_service.get_completed_activities_by_date_range") as mock_get_completed,
        ):

            mock_get_planned.return_value = mock_planned
            mock_get_completed.return_value = mock_completed
            # Fix: Ensure timezone information is kept when converting to string
            start_date_str = quote(yesterday.isoformat())
            end_date_str = quote((day_plus_2_event + timedelta(days=1)).isoformat())

            response = await client.get(
                f"/myactivities/activities/{athlete_id}?start_date={start_date_str}&end_date={end_date_str}"
            )

            assert response.status_code == 200
            data = response.json()
            assert "events" in data
            assert len(data["events"]) == 3

            # Assert correct chronological order
            assert data["events"][0]["title"] == mock_planned[0].name
            assert datetime.fromisoformat(data["events"][0]["date"]) == mock_planned[0].scheduled_date

            assert data["events"][1]["title"] == mock_completed[0].name
            assert datetime.fromisoformat(data["events"][1]["date"]) == mock_completed[0].start_date_local

            assert data["events"][2]["title"] == mock_completed[1].name
            assert datetime.fromisoformat(data["events"][2]["date"]) == mock_completed[1].start_date_local


@pytest.mark.asyncio
async def test_get_activities_missing_start_date():
    """Test retrieving a activities with a missing start_date query parameter."""
    async with mock_app() as client:
        athlete_id = uuid.uuid4()
        end_date = quote(datetime(2026, 1, 7, tzinfo=timezone.utc).isoformat())

        response = await client.get(
            f"/myactivities/activities/{athlete_id}?end_date={end_date}"
        )
        assert response.status_code == 422
        assert "detail" in response.json()
        assert "Field required" in response.json()["detail"][0]["msg"]

@pytest.mark.asyncio
async def test_get_activities_missing_end_date():
    """Test retrieving a activities with a missing end_date query parameter."""
    async with mock_app() as client:
        athlete_id = uuid.uuid4()
        start_date = quote(datetime(2026, 1, 1, tzinfo=timezone.utc).isoformat())

        response = await client.get(
            f"/myactivities/activities/{athlete_id}?start_date={start_date}"
        )
        assert response.status_code == 422
        assert "detail" in response.json()
        assert "Field required" in response.json()["detail"][0]["msg"]

@pytest.mark.asyncio
async def test_get_activities_same_start_end_date():
    """Test retrieving a activities where start_date is the same as end_date."""
    async with mock_app() as client:
        athlete_id = uuid.uuid4()
        single_date = datetime(2026, 1, 6, 12, 0, 0, tzinfo=timezone.utc)
        
        mock_planned = [
            mock_obj(
                id=uuid.uuid4(),
                athlete_id=athlete_id,
                name="Planned for today",
                type=ActivityType.run,
                goal=ActivityGoal.endurance,
                scheduled_date=single_date,
                completed=False,
                created_at=datetime.now(timezone.utc),
            )
        ]
        mock_completed = [
            mock_obj(
                id=uuid.uuid4(),
                athlete_id=athlete_id,
                name="Completed today",
                source=ActivitySource.STRAVA,
                sport_type="Ride",
                start_date=single_date,
                start_date_local=single_date,
                created_at=datetime.now(timezone.utc),
            )
        ]

        with (
            patch("app.services.planned_activity_service.get_planned_activities_by_date_range") as mock_get_planned,
            patch("app.services.completed_activity_service.get_completed_activities_by_date_range") as mock_get_completed,
        ):
            mock_get_planned.return_value = mock_planned
            mock_get_completed.return_value = mock_completed

            response = await client.get(
                f"/myactivities/activities/{athlete_id}?start_date={quote(single_date.isoformat())}&end_date={quote(single_date.isoformat())}"
            )

            assert response.status_code == 200
            data = response.json()
            assert "events" in data
            assert len(data["events"]) == 2 # Both activities on the same day

            # Assert correct order (planned before completed on the same day, or based on what service returns)
            assert data["events"][0]["title"] == mock_planned[0].name
            assert data["events"][1]["title"] == mock_completed[0].name

@pytest.mark.asyncio
async def test_get_activities_only_planned_activities():
    """Test retrieving a activities with only planned activities."""
    async with mock_app() as client:
        athlete_id = uuid.uuid4()
        start_date = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2026, 1, 7, tzinfo=timezone.utc)

        mock_planned = [
            mock_obj(
                id=uuid.uuid4(),
                athlete_id=athlete_id,
                name="Future Planned Run",
                type=ActivityType.run,
                scheduled_date=datetime(2026, 1, 3, tzinfo=timezone.utc),
                completed=False,
                created_at=datetime.now(timezone.utc),
            )
        ]

        with (
            patch("app.services.planned_activity_service.get_planned_activities_by_date_range") as mock_get_planned,
            patch("app.services.completed_activity_service.get_completed_activities_by_date_range") as mock_get_completed,
        ):
            mock_get_planned.return_value = mock_planned
            mock_get_completed.return_value = []

            response = await client.get(
                f"/myactivities/activities/{athlete_id}?start_date={quote(start_date.isoformat())}&end_date={quote(end_date.isoformat())}"
            )

            assert response.status_code == 200
            data = response.json()
            assert "events" in data
            assert len(data["events"]) == 1
            assert data["events"][0]["title"] == mock_planned[0].name
            assert data["events"][0]["status"] == "planned"

@pytest.mark.asyncio
async def test_get_activities_only_completed_activities():
    """Test retrieving a activities with only completed activities."""
    async with mock_app() as client:
        athlete_id = uuid.uuid4()
        start_date = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2026, 1, 7, tzinfo=timezone.utc)

        mock_completed = [
            mock_obj(
                id=uuid.uuid4(),
                athlete_id=athlete_id,
                name="Past Completed Ride",
                source=ActivitySource.STRAVA,
                sport_type="Ride",
                start_date=datetime(2026, 1, 4, tzinfo=timezone.utc),
                start_date_local=datetime(2026, 1, 4, tzinfo=timezone.utc),
                created_at=datetime.now(timezone.utc),
            )
        ]

        with (
            patch("app.services.planned_activity_service.get_planned_activities_by_date_range") as mock_get_planned,
            patch("app.services.completed_activity_service.get_completed_activities_by_date_range") as mock_get_completed,
        ):
            mock_get_planned.return_value = []
            mock_get_completed.return_value = mock_completed

            response = await client.get(
                f"/myactivities/activities/{athlete_id}?start_date={quote(start_date.isoformat())}&end_date={quote(end_date.isoformat())}"
            )

            assert response.status_code == 200
            data = response.json()
            assert "events" in data
            assert len(data["events"]) == 1
            assert data["events"][0]["title"] == mock_completed[0].name
            assert data["events"][0]["status"] == "completed"