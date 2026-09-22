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


@pytest.mark.asyncio
async def test_ai_client_fallback_and_custom_providers():
    from app.ai.client import AIClient

    with patch.dict("os.environ", {"AI_API_KEY": "", "AI_API_URL": "", "ANTHROPIC_API_KEY": "", "OPENAI_API_KEY": ""}, clear=True):
        client = AIClient()
        result = await client.generate_json("System prompt", "User prompt")
        assert "workouts" in result
        assert "reasoning" in result


    custom_client = AIClient(
        api_key="fake-custom-key",
        api_url="http://localhost:11434/v1",
    )
    assert custom_client.api_url == "http://localhost:11434/v1"
    assert custom_client.api_key == "fake-custom-key"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": '{"reasoning": "Local LLM plan", "workouts": []}'
                }
            }
        ]
    }
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        res = await custom_client.generate_json("sys", "usr")
        assert res["reasoning"] == "Local LLM plan"
        assert mock_post.call_args[1]["headers"]["Authorization"] == "Bearer fake-custom-key"

    anthropic_client = AIClient(
        api_key="fake-anthropic-key",
        api_url="https://api.anthropic.com/v1/messages",
    )
    mock_anthropic_resp = MagicMock()
    mock_anthropic_resp.status_code = 200
    mock_anthropic_resp.json.return_value = {
        "content": [
            {
                "text": '{"reasoning": "Anthropic plan", "workouts": []}'
            }
        ]
    }
    mock_anthropic_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_anthropic_resp
        res = await anthropic_client.generate_json("sys", "usr")
        assert res["reasoning"] == "Anthropic plan"
        assert mock_post.call_args[1]["headers"]["x-api-key"] == "fake-anthropic-key"

    model_client = AIClient(
        api_key="fake-key",
        api_url="http://localhost:11434/v1",
        model="llama3.2",
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        await model_client.generate_json("sys", "usr")
        assert mock_post.call_args[1]["json"]["model"] == "llama3.2"


@pytest.mark.asyncio
async def test_ai_generate_plan_preview_arbitrary_duration():
    """Test AI adaptive scheduling plan generation for arbitrary durations (e.g. 28 days / 1 month)."""
    custom_start = datetime(2026, 3, 1, 0, 0, 0, tzinfo=timezone.utc)
    async with mock_app() as client:
        with patch("app.api.routers.ai.generate_adaptive_plan", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = {
                "athlete_id": str(athlete_id),
                "start_date": custom_start.isoformat(),
                "duration_days": 28,
                "reasoning": "4-week periodized mesocycle",
                "workouts": [
                    {
                        "day_offset": i,
                        "planned_date": (custom_start + timedelta(days=i)).isoformat(),
                        "name": f"Workout Day {i}",
                        "sport_type": "Ride",
                        "duration_min": 60,
                    }
                    for i in range(28)
                ],
            }

            url = f"/myactivities/ai/generate-plan?athlete_id={athlete_id}&start_date={quote(custom_start.isoformat())}&duration_days=28"
            res = await client.post(url)
            assert res.status_code == 200
            data = res.json()
            assert data["duration_days"] == 28
            assert len(data["workouts"]) == 28
            assert data["workouts"][27]["name"] == "Workout Day 27"


@pytest.mark.asyncio
async def test_ai_confirm_plan_multi_week():
    """Test confirming a multi-week plan."""
    custom_start = datetime(2026, 3, 1, 0, 0, 0, tzinfo=timezone.utc)
    async with mock_app() as client:
        with patch("app.api.routers.ai.confirm_adaptive_plan", new_callable=AsyncMock) as mock_confirm:
            plan_id = uuid.uuid4()
            mock_plan = mock_obj(id=plan_id, status="confirmed")
            mock_confirm.return_value = mock_plan

            payload = {
                "athlete_id": str(athlete_id),
                "start_date": custom_start.isoformat(),
                "duration_days": 14,
                "reasoning": "Two-week block",
                "workouts": [
                    {
                        "day_offset": i,
                        "planned_date": (custom_start + timedelta(days=i)).isoformat(),
                        "name": f"Session {i}",
                        "sport_type": "Run",
                        "duration_min": 45,
                    }
                    for i in range(14)
                ],
            }

            res = await client.post("/myactivities/ai/confirm-plan", json=payload)
            assert res.status_code == 201
            assert res.json()["plan_id"] == str(plan_id)
            assert res.json()["status"] == "confirmed"


@pytest.mark.asyncio
async def test_ai_fallback_custom_durations():
    """Test AIClient fallback generation for 7 days and 28 days."""
    from app.ai.client import AIClient
    client = AIClient(api_url="")

    # 7-day test
    res_7 = await client.generate_json("System", "Generate 7-day schedule")
    assert len(res_7["workouts"]) == 7
    assert res_7["workouts"][0]["day_offset"] == 0
    assert res_7["workouts"][6]["day_offset"] == 6

    # 28-day test
    res_28 = await client.generate_json("System", "Duration: 28 days schedule")
    assert len(res_28["workouts"]) == 28
    assert res_28["workouts"][0]["day_offset"] == 0
    assert res_28["workouts"][27]["day_offset"] == 27
    assert res_28["workouts"][27]["plan_metadata"]["week_number"] == 4
    assert res_28["workouts"][27]["plan_metadata"]["is_deload"] is True


@pytest.mark.asyncio
async def test_ai_weekly_recap_with_duration():
    """Test AI recap with custom duration."""
    async with mock_app() as client:
        with patch("app.api.routers.ai.generate_weekly_recap", new_callable=AsyncMock) as mock_recap:
            mock_recap.return_value = {
                "athlete_id": str(athlete_id),
                "start_date": week_start.isoformat(),
                "duration_days": 14,
                "planned_sessions": 10,
                "completed_sessions": 8,
                "compliance_rate": 80.0,
                "total_completed_hours": 12.0,
                "summary": "Completed 8 sessions.",
            }

            url = f"/myactivities/ai/weekly-recap/{athlete_id}?week_start={quote(week_start.isoformat())}&duration_days=14"
            res = await client.get(url)
            assert res.status_code == 200
            assert res.json()["duration_days"] == 14
            assert res.json()["compliance_rate"] == 80.0


@pytest.mark.asyncio
async def test_ai_generate_and_confirm_plan_authenticated_self():
    """Test generating and confirming a plan using JWT authentication without athlete_id."""
    from app.services.auth_service import get_optional_current_athlete
    from app.models.athlete import Athlete

    mock_athlete = mock_obj(id=athlete_id, spec=Athlete)

    async with mock_app() as client:
        app.dependency_overrides[get_optional_current_athlete] = lambda: mock_athlete
        with patch("app.api.routers.ai.generate_adaptive_plan", new_callable=AsyncMock) as mock_gen, \
             patch("app.api.routers.ai.confirm_adaptive_plan", new_callable=AsyncMock) as mock_confirm:

            mock_gen.return_value = {
                "athlete_id": str(athlete_id),
                "start_date": week_start.isoformat(),
                "duration_days": 7,
                "reasoning": "Self-service plan",
                "workouts": [],
            }
            plan_id = uuid.uuid4()
            mock_confirm.return_value = mock_obj(id=plan_id, status="confirmed")

            # 1. Generate without athlete_id in URL
            gen_url = f"/myactivities/ai/generate-plan?start_date={quote(week_start.isoformat())}"
            res_gen = await client.post(gen_url, headers={"Authorization": "Bearer mock_token"})
            assert res_gen.status_code == 200
            assert res_gen.json()["athlete_id"] == str(athlete_id)

            # 2. Confirm without athlete_id in body
            conf_payload = {
                "start_date": week_start.isoformat(),
                "workouts": [],
            }
            res_conf = await client.post("/myactivities/ai/confirm-plan", json=conf_payload, headers={"Authorization": "Bearer mock_token"})
            assert res_conf.status_code == 201
            assert res_conf.json()["plan_id"] == str(plan_id)







