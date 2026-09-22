from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import uuid
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.athlete import Athlete
from app.models.activities import Activity, ActivityMetric, WeekPlan, TrainingPreference, ActivityStatus
from app.enums import ActivitySource
from app.ai.client import AIClient
from app.ai.load_analysis_service import calculate_athlete_training_load


async def generate_adaptive_plan(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    start_date: datetime,
    duration_days: int = 7,
) -> Dict[str, Any]:
    """
    Analyzes historical load and athlete constraints, generates preview plan for any start date and duration.
    Supports 7-day microcycles up to multi-week/monthly mesocycles (e.g. 28 days).
    """
    # 1. Fetch athlete and preferences
    res = await db.execute(
        select(Athlete)
        .where(Athlete.id == athlete_id)
        .options(selectinload(Athlete.training_preferences))
    )
    athlete = res.scalar_one_or_none()
    if not athlete:
        raise ValueError(f"Athlete {athlete_id} not found")

    prefs: Optional[TrainingPreference] = athlete.training_preferences
    load_summary = await calculate_athlete_training_load(db, athlete_id, days_back=28)

    period_type = (
        f"{duration_days}-day training mesocycle block (with progressive overload and periodized recovery/deload)"
        if duration_days > 7
        else f"{duration_days}-day training microcycle schedule"
    )

    system_prompt = (
        "You are an expert endurance sports coach specializing in adaptive training periodization. "
        f"Create a personalized {period_type} matching the athlete's load and preferences. "
        "Respond ONLY with a JSON object matching this schema:\n"
        "{\n"
        '  "reasoning": "string explaining the training periodization strategy",\n'
        '  "workouts": [\n'
        "    {\n"
        '      "day_offset": 0,\n'
        '      "name": "Base Endurance Ride",\n'
        '      "sport_type": "Ride",\n'
        '      "target_duration_min": 60,\n'
        '      "target_distance_m": 25000,\n'
        '      "target_intensity": 70,\n'
        '      "plan_metadata": {\n'
        '        "structure": {\n'
        '          "warmup": {"duration_min": 10, "description": "Easy spinning"},\n'
        '          "main_set": [{"intervals": 1, "duration_min": 40, "intensity": "Zone 2", "recovery_min": 0}],\n'
        '          "cooldown": {"duration_min": 10, "description": "Easy spinning"}\n'
        "        }\n"
        "      }\n"
        "    }\n"
        "  ]\n"
        "}"
    )

    user_prompt = f"""
Athlete: {athlete.name or 'Athlete'}
Weekly training hours target: {athlete.weekly_training_hours or 'Adaptive based on history'}
Max days per week: {prefs.max_days_per_week if prefs else 7}
Preferences: {prefs.sport_targets if prefs else {}}
Rest days preference: {prefs.rest_day_preference if prefs else []}
Recent 4-week load summary: {json.dumps(load_summary)}
Plan start date: {start_date.isoformat()}
Duration: {duration_days} days

Generate the JSON {duration_days}-day schedule (day_offset 0 to {duration_days - 1}).
"""

    client = AIClient()
    ai_output = await client.generate_json(system_prompt, user_prompt)

    workouts = []
    for item in ai_output.get("workouts", []):
        day_offset = item.get("day_offset", 0)
        workout_date = start_date + timedelta(days=day_offset)
        duration_val = item.get("target_duration_min") or item.get("duration_min", 60)
        dist_val = item.get("target_distance_m") or item.get("distance_m")
        intensity_val = item.get("target_intensity") or item.get("intensity")
        workouts.append({
            "day_offset": day_offset,
            "planned_date": workout_date.isoformat(),
            "name": item.get("name", "Training Session"),
            "sport_type": item.get("sport_type", "Ride"),
            "duration_min": duration_val,
            "distance_m": dist_val,
            "intensity": intensity_val,
            "plan_metadata": item.get("plan_metadata", {}),
        })

    return {
        "athlete_id": str(athlete_id),
        "start_date": start_date.isoformat(),
        "week_start_date": start_date.isoformat(),
        "duration_days": duration_days,
        "reasoning": ai_output.get("reasoning", "Adaptive progression based on recent volume."),
        "workouts": workouts,
    }


async def generate_adaptive_week_plan(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    target_week_start: datetime,
) -> Dict[str, Any]:
    """Backwards-compatible convenience wrapper for 7-day plans."""
    return await generate_adaptive_plan(db, athlete_id, start_date=target_week_start, duration_days=7)


async def confirm_adaptive_plan(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    plan_data: Dict[str, Any],
) -> WeekPlan:
    """
    Persists confirmed preview plan into WeekPlan container and Activity rows in DB.
    Works for any plan duration (e.g. 7 days, 14 days, 28-day month).
    """
    raw_start = plan_data.get("start_date") or plan_data.get("week_start_date")
    if raw_start:
        if isinstance(raw_start, datetime):
            start_date = raw_start
        else:
            start_date = datetime.fromisoformat(raw_start)
    else:
        start_date = datetime.now(timezone.utc)

    # Create WeekPlan container
    week_plan = WeekPlan(
        athlete_id=athlete_id,
        week_start_date=start_date,
        status="confirmed",
        ai_reasoning=plan_data.get("reasoning"),
    )
    db.add(week_plan)
    await db.flush()

    for item in plan_data.get("workouts", []):
        if "planned_date" in item and item["planned_date"]:
            if isinstance(item["planned_date"], datetime):
                planned_dt = item["planned_date"]
            else:
                planned_dt = datetime.fromisoformat(item["planned_date"])
        else:
            day_offset = item.get("day_offset", 0)
            planned_dt = start_date + timedelta(days=day_offset)

        duration_val = item.get("duration_min") or item.get("target_duration_min")
        distance_val = item.get("distance_m") or item.get("target_distance_m")
        intensity_val = item.get("intensity") or item.get("target_intensity")

        activity = Activity(
            athlete_id=athlete_id,
            week_plan_id=week_plan.id,
            source=ActivitySource.ai_generated,
            status=ActivityStatus.planned,
            name=item.get("name"),
            sport_type=item.get("sport_type"),
            planned_date=planned_dt,
            duration_min=duration_val,
            distance_m=distance_val,
            intensity=intensity_val,
            plan_metadata=item.get("plan_metadata", {}),
        )
        db.add(activity)

    await db.commit()
    await db.refresh(week_plan)
    return week_plan


async def confirm_adaptive_week_plan(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    plan_data: Dict[str, Any],
) -> WeekPlan:
    """Backwards-compatible convenience wrapper."""
    return await confirm_adaptive_plan(db, athlete_id, plan_data)


async def generate_weekly_recap(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    week_start: datetime,
    duration_days: int = 7,
) -> Dict[str, Any]:
    """
    Compares completed vs planned activities for the designated time window.
    Includes planned, completed (including unplanned completed), missed, and modified activities.
    """
    from sqlalchemy import or_, and_
    week_end = week_start + timedelta(days=duration_days)

    # Query activities for that period (checking both planned_date and actual_date)
    result = await db.execute(
        select(Activity)
        .where(
            Activity.athlete_id == athlete_id,
            or_(
                and_(
                    Activity.planned_date.isnot(None),
                    Activity.planned_date >= week_start,
                    Activity.planned_date < week_end,
                ),
                and_(
                    Activity.actual_date.isnot(None),
                    Activity.actual_date >= week_start,
                    Activity.actual_date < week_end,
                ),
            ),
        )
        .options(selectinload(Activity.metrics))
    )
    activities = result.scalars().all()

    planned_count = sum(1 for a in activities if a.status in [ActivityStatus.planned, ActivityStatus.missed])
    completed_count = sum(1 for a in activities if a.status in [ActivityStatus.completed, ActivityStatus.modified])
    total_completed_min = sum(
        ((a.metrics.duration_min if a.metrics and a.metrics.duration_min else a.duration_min) or 0)
        for a in activities if a.status in [ActivityStatus.completed, ActivityStatus.modified]
    )

    total_target = planned_count + completed_count
    compliance = round(completed_count / total_target * 100, 1) if total_target > 0 else 100.0

    return {
        "athlete_id": str(athlete_id),
        "start_date": week_start.isoformat(),
        "end_date": week_end.isoformat(),
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "duration_days": duration_days,
        "planned_sessions": planned_count,
        "completed_sessions": completed_count,
        "compliance_rate": compliance,
        "total_completed_hours": round(total_completed_min / 60.0, 2),
        "summary": f"Completed {completed_count} sessions totaling {round(total_completed_min / 60.0, 1)} hours.",
    }

