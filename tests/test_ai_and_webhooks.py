import pytest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from urllib.parse import quote

from conftest import mock_app, mock_obj
from app.main import app

athlete_id = uuid.uuid4()
week_start = datetime(2026, 1, 5, 0, 0, 0, tzinfo=timezone.utc)


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
async def test_strava_sync_authenticated():
    """Test on-demand Strava sync using JWT authentication without athlete_id parameter."""
    from app.services.auth_service import get_optional_current_athlete
    from app.models.athlete import Athlete

    mock_athlete = mock_obj(id=athlete_id, spec=Athlete)

    async with mock_app() as client:
        app.dependency_overrides[get_optional_current_athlete] = lambda: mock_athlete
        with patch("app.services.strava_sync_service.sync_athlete_activities", new_callable=AsyncMock) as mock_sync:
            mock_sync.return_value = {
                "processed": 5,
                "new": 2,
                "skipped": 3,
                "last_synced_at": datetime.now(timezone.utc).isoformat(),
            }
            res = await client.post("/myactivities/strava/sync", headers={"Authorization": "Bearer mock_token"})
            assert res.status_code == 200
            data = res.json()
            assert data["processed"] == 5
            assert data["new"] == 2
            mock_sync.assert_called_once()


@pytest.mark.asyncio
async def test_strava_oauth_callback_authenticated():
    """Test Strava OAuth callback inferring athlete_id from Bearer token."""
    from app.services.auth_service import get_optional_current_athlete
    from app.models.athlete import Athlete

    mock_athlete = mock_obj(id=athlete_id, spec=Athlete)

    async with mock_app() as client:
        app.dependency_overrides[get_optional_current_athlete] = lambda: mock_athlete
        with patch("app.services.athlete_service.handle_strava_oauth_callback", new_callable=AsyncMock) as mock_oauth:
            mock_oauth.return_value = {
                "access_token": "jwt_token_123",
                "athlete_id": str(athlete_id),
                "connected": True,
            }
            res = await client.post("/myactivities/strava/oauth/callback?code=mock_strava_code")
            assert res.status_code == 200
            data = res.json()
            assert data["connected"] is True
            mock_oauth.assert_called_once_with(mock_oauth.call_args[0][0], athlete_id, "mock_strava_code")


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


@pytest.mark.asyncio
async def test_ai_plan_honors_preferences_and_sports():
    """Verify that AI plan generation strictly honors athlete preferred sports, rest days, and volume."""
    from app.ai.planner_service import generate_adaptive_plan

    # Monday start date (2026-03-02 was a Monday)
    monday_start = datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc)
    mock_prefs = mock_obj(
        max_days_per_week=5,
        rest_day_preference=["Monday", "Friday"],
        split_notes="Targeting sub-40min 10k",
        sport_targets={},
    )
    mock_athlete = mock_obj(
        id=athlete_id,
        name="Runner Alex",
        preferred_sports=["Run"],
        weekly_training_hours=7.0,
        training_preferences=mock_prefs,
        ftp=None,
        threshold_pace=4.2,
        weight=68.0,
        max_hr=195,
        lthr=174,
    )

    mock_db = AsyncMock()
    mock_db.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=mock_athlete))

    with patch.dict("os.environ", {"AI_API_KEY": "", "AI_API_URL": ""}, clear=True):
        plan = await generate_adaptive_plan(
            mock_db,
            athlete_id,
            start_date=monday_start,
            duration_days=7,
            user_prompt="Focus on 10k interval pace",
        )

    assert len(plan["workouts"]) == 7

    # Day 0 (Monday) should be rest day
    assert plan["workouts"][0]["sport_type"] == "Other"
    assert "Rest" in plan["workouts"][0]["name"]
    assert plan["workouts"][0]["duration_min"] == 0

    # Day 4 (Friday) should be rest day
    assert plan["workouts"][4]["sport_type"] == "Other"
    assert "Rest" in plan["workouts"][4]["name"]
    assert plan["workouts"][4]["duration_min"] == 0

    # Active days MUST all be 'Run' (since preferred_sports=['Run'])
    active_workouts = [w for w in plan["workouts"] if w["duration_min"] > 0]
    assert len(active_workouts) == 5  # Exactly 5 active days (max_days=5, 2 rest days)
    for w in active_workouts:
        assert w["sport_type"] == "Run"
        assert w["sport_type"] != "Ride"

    # Volume should sum close to 7 hours = 420 minutes (±15%)
    total_minutes = sum(w["duration_min"] for w in active_workouts)
    assert 350 <= total_minutes <= 490

    # Reasoning incorporates athlete preferences
    assert "Run" in plan["reasoning"]


@pytest.mark.asyncio
async def test_ai_plan_guardrails_sanitize_rogue_sports():
    """Verify that planner_service guardrails catch rogue sports and enforce rest days even if LLM outputs Ride."""
    from app.ai.planner_service import generate_adaptive_plan

    monday_start = datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc)
    mock_prefs = mock_obj(
        max_days_per_week=6,
        rest_day_preference=["Friday"],
        split_notes="Strength and running only",
        sport_targets={},
    )
    mock_athlete = mock_obj(
        id=athlete_id,
        name="Hybrid Athlete",
        preferred_sports=["Run", "WeightTraining"],
        weekly_training_hours=6.0,
        training_preferences=mock_prefs,
        ftp=None,
        threshold_pace=None,
        weight=75.0,
        max_hr=None,
        lthr=None,
    )

    mock_db = AsyncMock()
    mock_db.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=mock_athlete))

    # Simulate an LLM that ignored instructions and produced "Ride" sessions
    rogue_ai_output = {
        "reasoning": "Rogue plan with bike rides",
        "workouts": [
            {"day_offset": 0, "name": "Long Ride", "sport_type": "Ride", "target_duration_min": 90, "target_intensity": 70},
            {"day_offset": 1, "name": "Run Intervals", "sport_type": "Run", "target_duration_min": 60, "target_intensity": 80},
            {"day_offset": 2, "name": "Recovery Ride", "sport_type": "Ride", "target_duration_min": 45, "target_intensity": 60},
            {"day_offset": 3, "name": "Heavy Lift", "sport_type": "WeightTraining", "target_duration_min": 60, "target_intensity": 85},
            {"day_offset": 4, "name": "Friday Big Ride", "sport_type": "Ride", "target_duration_min": 120, "target_intensity": 80},  # Should be forced to rest!
            {"day_offset": 5, "name": "Weekend Bike Tour", "sport_type": "Ride", "target_duration_min": 100, "target_intensity": 75},
            {"day_offset": 6, "name": "Mobility Lift", "sport_type": "WeightTraining", "target_duration_min": 45, "target_intensity": 60},
        ],
    }

    with patch("app.ai.planner_service.AIClient.generate_json", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = rogue_ai_output
        plan = await generate_adaptive_plan(
            mock_db,
            athlete_id,
            start_date=monday_start,
            duration_days=7,
        )

    assert len(plan["workouts"]) == 7

    # Friday (Day 4) must be converted to rest despite LLM outputting 120m Friday Big Ride
    friday = plan["workouts"][4]
    assert friday["sport_type"] == "Other"
    assert friday["name"] == "Rest & Recovery"
    assert friday["duration_min"] == 0

    # NO workout may have sport_type "Ride"
    for w in plan["workouts"]:
        assert w["sport_type"] != "Ride", f"Rogue sport was not sanitized: {w}"
        if w["duration_min"] > 0:
            assert w["sport_type"] in ["Run", "WeightTraining"]


@pytest.mark.asyncio
async def test_ai_remove_specific_workout_and_replace_existing():
    """Verify AI coach can remove specific planned workouts and replace existing ones without duplicating."""
    from app.ai.planner_service import generate_adaptive_plan, confirm_adaptive_plan
    from app.models.activities import ActivityStatus

    monday_start = datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc)
    wednesday_dt = monday_start + timedelta(days=2)
    mon_id = uuid.uuid4()
    wed_id = uuid.uuid4()

    existing_mon = mock_obj(
        id=mon_id,
        name="Easy Run",
        sport_type="Run",
        planned_date=monday_start,
        duration_min=40,
        status=ActivityStatus.planned,
    )
    existing_wed = mock_obj(
        id=wed_id,
        name="Tempo Run",
        sport_type="Run",
        planned_date=wednesday_dt,
        duration_min=50,
        status=ActivityStatus.planned,
    )

    mock_prefs = mock_obj(
        max_days_per_week=6,
        rest_day_preference=[],
        split_notes="",
        sport_targets={},
    )
    mock_athlete = mock_obj(
        id=athlete_id,
        name="Alex",
        preferred_sports=["Run"],
        weekly_training_hours=5.0,
        training_preferences=mock_prefs,
        ftp=None,
        threshold_pace=None,
        weight=70.0,
        max_hr=None,
        lthr=None,
    )

    def make_db():
        db = AsyncMock()
        # 1st execute: Athlete query -> scalar_one_or_none
        # 2nd execute (inside calculate_athlete_training_load): activities -> scalars().all() = []
        # 3rd execute: existing_planned -> scalars().all() = [existing_mon, existing_wed]
        res_athlete = MagicMock(scalar_one_or_none=MagicMock(return_value=mock_athlete))
        res_load = MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))))
        res_existing = MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[existing_mon, existing_wed]))))
        db.execute.side_effect = [res_athlete, res_load, res_existing]
        return db

    # 1. Remove only Wednesday's workout (including wording with "plan" / "planned")
    with patch.dict("os.environ", {"AI_API_KEY": "", "AI_API_URL": ""}, clear=True):
        remove_plan = await generate_adaptive_plan(
            make_db(),
            athlete_id,
            start_date=monday_start,
            duration_days=7,
            user_prompt="Remove Wednesday's workout from my plan",
        )

    assert remove_plan["workouts"] == []
    assert remove_plan["remove_workout_ids"] == [str(wed_id)]
    assert len(remove_plan["removed_workouts"]) == 1
    assert remove_plan["removed_workouts"][0]["name"] == "Tempo Run"

    # 2. Change/regenerate this week's workouts -> existing overlapping planned workouts are marked for removal
    with patch.dict("os.environ", {"AI_API_KEY": "", "AI_API_URL": ""}, clear=True):
        replace_plan = await generate_adaptive_plan(
            make_db(),
            athlete_id,
            start_date=monday_start,
            duration_days=7,
            user_prompt="Change this week to easy aerobic runs",
        )

    assert len(replace_plan["workouts"]) == 7
    assert set(replace_plan["remove_workout_ids"]) == {str(mon_id), str(wed_id)}

    # 3. Confirming removal-only plan executes delete and commits without adding workouts
    confirm_db = AsyncMock()
    confirm_db.add = MagicMock()
    await confirm_adaptive_plan(
        confirm_db,
        athlete_id,
        {
            "start_date": monday_start.isoformat(),
            "duration_days": 7,
            "reasoning": "Removed Wednesday workout",
            "remove_workout_ids": [str(wed_id)],
            "workouts": [],
        },
    )
    assert confirm_db.execute.await_count == 1
    confirm_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_ai_dynamic_add_and_two_workouts_per_day():
    """Verify AI coach can dynamically add a gym session on Monday or two workouts on one day without rewriting the week."""
    from app.ai.planner_service import generate_adaptive_plan
    from app.models.activities import ActivityStatus

    monday_start = datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc)
    mon_id = uuid.uuid4()
    wed_id = uuid.uuid4()

    existing_mon = mock_obj(
        id=mon_id,
        name="Easy Run",
        sport_type="Run",
        planned_date=monday_start,
        duration_min=40,
        status=ActivityStatus.planned,
    )
    existing_wed = mock_obj(
        id=wed_id,
        name="Tempo Run",
        sport_type="Run",
        planned_date=monday_start + timedelta(days=2),
        duration_min=50,
        status=ActivityStatus.planned,
    )

    mock_prefs = mock_obj(
        max_days_per_week=6,
        rest_day_preference=["Monday"],
        split_notes="",
        sport_targets={},
    )
    mock_athlete = mock_obj(
        id=athlete_id,
        name="Alex",
        preferred_sports=["Run", "Ride"],
        weekly_training_hours=6.0,
        training_preferences=mock_prefs,
        ftp=None,
        threshold_pace=None,
        weight=70.0,
        max_hr=None,
        lthr=None,
    )

    def make_db():
        db = AsyncMock()
        res_athlete = MagicMock(scalar_one_or_none=MagicMock(return_value=mock_athlete))
        res_load = MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))))
        res_existing = MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[existing_mon, existing_wed]))))
        db.execute.side_effect = [res_athlete, res_load, res_existing]
        return db

    # 1. Add gym session on Monday -> only 1 WeightTraining workout on Monday, 0 removals
    with patch.dict("os.environ", {"AI_API_KEY": "", "AI_API_URL": ""}, clear=True):
        add_gym_plan = await generate_adaptive_plan(
            make_db(),
            athlete_id,
            start_date=monday_start,
            duration_days=7,
            user_prompt="Add a gym session for Monday",
        )

    assert len(add_gym_plan["workouts"]) == 1
    assert add_gym_plan["workouts"][0]["day_offset"] == 0
    assert add_gym_plan["workouts"][0]["sport_type"] == "WeightTraining"
    assert add_gym_plan["remove_workout_ids"] == []

    # 2. Ask for two workouts on Tuesday -> 2 workouts on Tuesday, 0 removals
    with patch.dict("os.environ", {"AI_API_KEY": "", "AI_API_URL": ""}, clear=True):
        two_a_day_plan = await generate_adaptive_plan(
            make_db(),
            athlete_id,
            start_date=monday_start,
            duration_days=7,
            user_prompt="Add two workouts on Tuesday",
        )

    assert len(two_a_day_plan["workouts"]) == 2
    assert all(w["day_offset"] == 1 for w in two_a_day_plan["workouts"])
    assert two_a_day_plan["remove_workout_ids"] == []

    # 3. Targeted swap on Monday only -> replaces Monday only, leaves Wednesday alone
    with patch.dict("os.environ", {"AI_API_KEY": "", "AI_API_URL": ""}, clear=True):
        swap_mon_plan = await generate_adaptive_plan(
            make_db(),
            athlete_id,
            start_date=monday_start,
            duration_days=7,
            user_prompt="Change Monday's workout to a swim",
        )

    assert len(swap_mon_plan["workouts"]) == 1
    assert swap_mon_plan["workouts"][0]["day_offset"] == 0
    assert swap_mon_plan["workouts"][0]["sport_type"] == "Swim"
    assert swap_mon_plan["remove_workout_ids"] == [str(mon_id)]











