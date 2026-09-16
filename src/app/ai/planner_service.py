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


async def generate_adaptive_week_plan(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    target_week_start: datetime,
) -> Dict[str, Any]:
    """
    Analyzes historical load and athlete constraints, generates preview for next week.
    Returns preview data for user confirmation.
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

    system_prompt = (
        "You are an expert endurance sports coach specializing in adaptive training periodization. "
        "Create a personalized 7-day training schedule matching the athlete's load and preferences. "
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
Week start date: {target_week_start.isoformat()}

Generate the JSON 7-day schedule (day_offset 0 to 6).
"""

    client = AIClient()
    ai_output = await client.generate_json(system_prompt, user_prompt)

    workouts = []
    for item in ai_output.get("workouts", []):
        day_offset = item.get("day_offset", 0)
        workout_date = target_week_start + timedelta(days=day_offset)
        workouts.append({
            "day_offset": day_offset,
            "planned_date": workout_date.isoformat(),
            "name": item.get("name", "Training Session"),
            "sport_type": item.get("sport_type", "Ride"),
            "duration_min": item.get("target_duration_min", 60),
            "distance_m": item.get("target_distance_m"),
            "intensity": item.get("target_intensity"),
            "plan_metadata": item.get("plan_metadata", {}),
        })

    return {
        "athlete_id": str(athlete_id),
        "week_start_date": target_week_start.isoformat(),
        "reasoning": ai_output.get("reasoning", "Adaptive progression based on recent volume."),
        "workouts": workouts,
    }


async def confirm_adaptive_week_plan(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    plan_data: Dict[str, Any],
) -> WeekPlan:
    """
    Persists confirmed preview plan into WeekPlan and 7 Activity rows in DB.
    """
    week_start = datetime.fromisoformat(plan_data["week_start_date"])

    # Create WeekPlan container
    week_plan = WeekPlan(
        athlete_id=athlete_id,
        week_start_date=week_start,
        status="confirmed",
        ai_reasoning=plan_data.get("reasoning"),
    )
    db.add(week_plan)
    await db.flush()

    for item in plan_data.get("workouts", []):
        planned_dt = datetime.fromisoformat(item["planned_date"])
        activity = Activity(
            athlete_id=athlete_id,
            week_plan_id=week_plan.id,
            source=ActivitySource.ai_generated,
            status=ActivityStatus.planned,
            name=item.get("name"),
            sport_type=item.get("sport_type"),
            planned_date=planned_dt,
            duration_min=item.get("duration_min"),
            distance_m=item.get("distance_m"),
            intensity=item.get("intensity"),
            plan_metadata=item.get("plan_metadata", {}),
        )
        db.add(activity)

    await db.commit()
    await db.refresh(week_plan)
    return week_plan


async def generate_weekly_recap(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    week_start: datetime,
) -> Dict[str, Any]:
    """
    Compares completed vs planned activities for the designated week.
    Includes planned, completed (including unplanned completed), missed, and modified activities.
    """
    from sqlalchemy import or_, and_
    week_end = week_start + timedelta(days=7)

    # Query activities for that week (checking both planned_date and actual_date)
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
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "planned_sessions": planned_count,
        "completed_sessions": completed_count,
        "compliance_rate": compliance,
        "total_completed_hours": round(total_completed_min / 60.0, 2),
        "summary": f"Completed {completed_count} sessions totaling {round(total_completed_min / 60.0, 1)} hours.",
    }
