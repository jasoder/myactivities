import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock

from conftest import mock_app, make_mock_athlete as _base_mock_athlete
from app.main import app
from app.services.auth_service import get_current_athlete


def make_mock_athlete(athlete_id=None, email="user@example.com", name="Test User"):
    return _base_mock_athlete(
        athlete_id=athlete_id,
        email=email,
        name=name,
        ftp=250,
        threshold_pace=4.2,
        weight=72.5,
        max_hr=190,
        lthr=172,
        preferred_sports=["Run", "Ride"],
        timezone_str="Europe/Helsinki",
        weekly_training_hours=8.5,
    )


@pytest.mark.asyncio
async def test_get_user_unauthorized():
    async with mock_app() as client:
        res = await client.get("/myactivities/user")
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_user_success():
    test_id = uuid.uuid4()
    mock_athlete = make_mock_athlete(athlete_id=test_id, email="runner@example.com", name="Jane Runner")

    async with mock_app() as client:
        app.dependency_overrides[get_current_athlete] = lambda: mock_athlete
        try:
            res = await client.get(
                "/myactivities/user",
                headers={"Authorization": "Bearer mock_token"},
            )
            assert res.status_code == 200
            data = res.json()
            assert data["id"] == str(test_id)
            assert data["email"] == "runner@example.com"
            assert data["name"] == "Jane Runner"
            assert data["ftp"] == 250
            assert "hashed_password" not in data
            assert "access_token" not in data
        finally:
            app.dependency_overrides.pop(get_current_athlete, None)


@pytest.mark.asyncio
async def test_update_user_profile():
    test_id = uuid.uuid4()
    mock_athlete = make_mock_athlete(athlete_id=test_id, email="runner@example.com", name="Original")

    async with mock_app() as client:
        app.dependency_overrides[get_current_athlete] = lambda: mock_athlete
        with patch("app.services.athlete_service.update_existing_athlete") as mock_update:
            updated_athlete = make_mock_athlete(athlete_id=test_id, email="runner@example.com", name="Updated Name")
            updated_athlete.weight = 70.0
            mock_update.return_value = updated_athlete

            try:
                res = await client.put(
                    "/myactivities/user",
                    json={"name": "Updated Name", "weight": 70.0},
                    headers={"Authorization": "Bearer mock_token"},
                )
                assert res.status_code == 200
                data = res.json()
                assert data["name"] == "Updated Name"
                assert data["weight"] == 70.0
            finally:
                app.dependency_overrides.pop(get_current_athlete, None)


@pytest.mark.asyncio
async def test_delete_user_account():
    test_id = uuid.uuid4()
    mock_athlete = make_mock_athlete(athlete_id=test_id)

    async with mock_app() as client:
        app.dependency_overrides[get_current_athlete] = lambda: mock_athlete
        with patch("app.services.athlete_service.delete_athlete_by_id") as mock_del:
            mock_del.return_value = True
            try:
                res = await client.delete(
                    "/myactivities/user",
                    headers={"Authorization": "Bearer mock_token"},
                )
                assert res.status_code == 204
                mock_del.assert_called_once()
            finally:
                app.dependency_overrides.pop(get_current_athlete, None)


@pytest.mark.asyncio
async def test_get_user_preferences():
    test_id = uuid.uuid4()
    mock_athlete = make_mock_athlete(athlete_id=test_id)

    async with mock_app() as client:
        app.dependency_overrides[get_current_athlete] = lambda: mock_athlete
        with patch("app.services.athlete_service.get_or_create_training_preferences") as mock_pref:
            mock_pref.return_value = MagicMock(
                athlete_id=test_id,
                max_days_per_week=5,
                sport_targets={"Run": 3, "Ride": 2},
                split_notes="3 runs, 2 rides",
                rest_day_preference=["monday", "friday"],
                updated_at=datetime.now(timezone.utc),
            )
            try:
                res = await client.get(
                    "/myactivities/user/preferences",
                    headers={"Authorization": "Bearer mock_token"},
                )
                assert res.status_code == 200
                data = res.json()
                assert data["max_days_per_week"] == 5
                assert data["sport_targets"] == {"Run": 3, "Ride": 2}
            finally:
                app.dependency_overrides.pop(get_current_athlete, None)


@pytest.mark.asyncio
async def test_update_user_preferences():
    test_id = uuid.uuid4()
    mock_athlete = make_mock_athlete(athlete_id=test_id)

    async with mock_app() as client:
        app.dependency_overrides[get_current_athlete] = lambda: mock_athlete
        with patch("app.services.athlete_service.update_training_preferences") as mock_pref:
            mock_pref.return_value = MagicMock(
                athlete_id=test_id,
                max_days_per_week=6,
                sport_targets={"Ride": 4},
                split_notes="Focus on cycling",
                rest_day_preference=["sunday"],
                updated_at=datetime.now(timezone.utc),
            )
            try:
                res = await client.put(
                    "/myactivities/user/preferences",
                    json={"max_days_per_week": 6, "sport_targets": {"Ride": 4}},
                    headers={"Authorization": "Bearer mock_token"},
                )
                assert res.status_code == 200
                data = res.json()
                assert data["max_days_per_week"] == 6
                assert data["sport_targets"] == {"Ride": 4}
            finally:
                app.dependency_overrides.pop(get_current_athlete, None)


@pytest.mark.asyncio
async def test_get_user_activities():
    test_id = uuid.uuid4()
    mock_athlete = make_mock_athlete(athlete_id=test_id)
    start_dt = datetime(2026, 9, 1, 0, 0, 0, tzinfo=timezone.utc)
    end_dt = datetime(2026, 9, 30, 23, 59, 59, tzinfo=timezone.utc)

    async with mock_app() as client:
        app.dependency_overrides[get_current_athlete] = lambda: mock_athlete
        with patch("app.services.activities_service.get_activities_events", new_callable=AsyncMock) as mock_events:
            from app.schemas.activities import ActivitiesEntry, ActivitiesSummary
            act_id = uuid.uuid4()
            mock_events.return_value = [
                ActivitiesEntry(
                    id=act_id,
                    date=start_dt,
                    title="Morning Run",
                    type="Run",
                    status="completed",
                    data=ActivitiesSummary(distance_m=5000.0, duration_s=1800, training_load=65.0),
                )
            ]
            try:
                from urllib.parse import quote
                res = await client.get(
                    f"/myactivities/user/activities?start_date={quote(start_dt.isoformat())}&end_date={quote(end_dt.isoformat())}",
                    headers={"Authorization": "Bearer mock_token"},
                )
                assert res.status_code == 200
                data = res.json()
                assert len(data["events"]) == 1
                assert data["events"][0]["title"] == "Morning Run"
                assert data["events"][0]["type"] == "Run"
                assert data["events"][0]["data"]["distance_m"] == 5000.0
            finally:
                app.dependency_overrides.pop(get_current_athlete, None)


@pytest.mark.asyncio
async def test_disconnect_user_strava():
    test_id = uuid.uuid4()
    mock_athlete = make_mock_athlete(athlete_id=test_id)
    mock_athlete.strava_id = "123456"

    async with mock_app() as client:
        app.dependency_overrides[get_current_athlete] = lambda: mock_athlete
        with patch("app.services.athlete_service.disconnect_strava", new_callable=AsyncMock) as mock_disc:
            try:
                res = await client.delete(
                    "/myactivities/user/strava",
                    headers={"Authorization": "Bearer mock_token"},
                )
                assert res.status_code == 204
                mock_disc.assert_called_once()
            finally:
                app.dependency_overrides.pop(get_current_athlete, None)


