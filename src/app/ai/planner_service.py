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
from app.services import athlete_service


async def generate_adaptive_plan(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    start_date: datetime,
    duration_days: int = 7,
    user_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyzes historical load and athlete constraints, generates preview plan for any start date and duration.
    Strictly incorporates athlete preferred sports, rest days, weekly volume, max days per week, and custom prompt.
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
    if not prefs:
        prefs = await athlete_service.get_or_create_training_preferences(db, athlete.id)

    load_summary = await calculate_athlete_training_load(db, athlete_id, days_back=28)

    preferred_sports = athlete.preferred_sports or ["Run", "Ride"]
    weekly_hours = athlete.weekly_training_hours if athlete.weekly_training_hours is not None else 6.0
    max_days = prefs.max_days_per_week if prefs and prefs.max_days_per_week is not None else 6
    rest_days = prefs.rest_day_preference or []
    split_notes = prefs.split_notes or ""
    sport_targets = prefs.sport_targets or {}

    # Map out calendar days with dates and designated rest days
    calendar_days = []
    for day in range(duration_days):
        day_date = start_date + timedelta(days=day)
        weekday_name = day_date.strftime("%A")
        is_rest = weekday_name in rest_days
        calendar_days.append(
            f"Day offset {day}: {day_date.strftime('%Y-%m-%d')} ({weekday_name}) - {'REST DAY' if is_rest else 'Active training eligible'}"
        )
    calendar_context = "\n".join(calendar_days)

    period_type = (
        f"{duration_days}-day training mesocycle block (with progressive overload and periodized recovery/deload)"
        if duration_days > 7
        else f"{duration_days}-day training microcycle schedule"
    )

    system_prompt = (
        "You are an expert endurance sports coach specializing in adaptive training periodization. "
        f"Create a personalized {period_type} matching the athlete's load and preferences.\n\n"
        "STRICT COACHING CONSTRAINTS:\n"
        f"1. SPORTS: You MUST ONLY prescribe workouts for sports listed in the athlete's Preferred Sports list: {preferred_sports}. "
        "Do NOT schedule any other sports. If only one sport is listed, every active workout must be that sport.\n"
        f"2. REST DAYS: The athlete has designated these rest days: {rest_days}. On these days, you MUST schedule complete rest "
        "(name: 'Rest & Recovery', sport_type: 'Other', target_duration_min: 0, target_intensity: 0) or light active recovery/mobility (max 20 min). "
        "Never schedule hard or normal workouts on designated rest days.\n"
        f"3. FREQUENCY: Do NOT exceed {max_days} active training sessions in any 7-day period.\n"
        f"4. VOLUME: Total workout minutes across each 7-day week must approximately equal {int(weekly_hours * 60)} minutes ({weekly_hours} hours) ±10%.\n"
        f"5. FOCUS & NOTES: Incorporate the athlete's training focus ({split_notes}) and specific user request into session designs.\n"
        "6. METRICS: Use the athlete's FTP, threshold pace, max HR, and LTHR to calibrate intensity zones and targets.\n\n"
        "Respond ONLY with a JSON object matching this schema:\n"
        "{\n"
        '  "reasoning": "string explaining how the plan fulfills the athlete\'s preferences, volume targets, and periodization strategy",\n'
        '  "workouts": [\n'
        "    {\n"
        '      "day_offset": 0,\n'
        '      "name": "Session Name",\n'
        '      "sport_type": "Run",\n'
        '      "target_duration_min": 60,\n'
        '      "target_distance_m": 10000,\n'
        '      "target_intensity": 75,\n'
        '      "plan_metadata": {\n'
        '        "structure": {\n'
        '          "warmup": {"duration_min": 10, "description": "Easy warm-up"},\n'
        '          "main_set": [{"intervals": 4, "duration_min": 5, "intensity": "Zone 4 Threshold", "recovery_min": 2}],\n'
        '          "cooldown": {"duration_min": 10, "description": "Easy cool-down"}\n'
        "        },\n"
        '        "target_duration_min": 60,\n'
        '        "target_intensity": 75,\n'
        '        "reasoning": "Targeted endurance stimulus"\n'
        "      }\n"
        "    }\n"
        "  ]\n"
        "}"
    )

    user_prompt_text = f"""
Athlete: {athlete.name or 'Athlete'}
Preferred Sports: {preferred_sports}
Weekly Training Hours Target: {weekly_hours} hours/week ({int(weekly_hours * 60)} minutes/week)
Max Days Per Week: {max_days} days/week
Designated Rest Days: {rest_days}
Training Focus & Split Notes: {split_notes or 'None specified'}
Athlete Request / Chat Prompt: {user_prompt or 'None specified'}
Performance Metrics: FTP={athlete.ftp or 'N/A'}W, Pace={athlete.threshold_pace or 'N/A'} min/km, Weight={athlete.weight or 'N/A'}kg, MaxHR={athlete.max_hr or 'N/A'}bpm, LTHR={athlete.lthr or 'N/A'}bpm
Sport Targets: {sport_targets}
Recent 4-week load summary: {json.dumps(load_summary)}
Plan start date: {start_date.isoformat()}
Duration: {duration_days} days

Calendar Days to Schedule:
{calendar_context}

Generate the JSON {duration_days}-day schedule (day_offset 0 to {duration_days - 1}).
"""

    client = AIClient()
    ai_output = await client.generate_json(system_prompt, user_prompt_text)

    workouts = []
    for item in ai_output.get("workouts", []):
        day_offset = item.get("day_offset", 0)
        workout_date = start_date + timedelta(days=day_offset)
        duration_val = item.get("target_duration_min") or item.get("duration_min", 0)
        dist_val = item.get("target_distance_m") or item.get("distance_m")
        intensity_val = item.get("target_intensity") or item.get("intensity")
        sport_val = item.get("sport_type") or (preferred_sports[0] if preferred_sports else "Run")
        name_val = item.get("name", "Training Session")
        meta_val = item.get("plan_metadata", {})

        # Guardrail: Enforce designated rest days
        day_name = workout_date.strftime("%A")
        if day_name in rest_days:
            sport_val = "Other"
            name_val = "Rest & Recovery"
            duration_val = 0
            dist_val = None
            intensity_val = 0
            meta_val = {
                "structure": {"rest": True},
                "target_duration_min": 0,
                "reasoning": f"Designated rest day ({day_name})",
            }
        elif preferred_sports and sport_val != "Other" and sport_val not in preferred_sports:
            # Guardrail: Never allow sports not in athlete's preferred sports list
            sport_val = preferred_sports[day_offset % len(preferred_sports)]
            if "Ride" in name_val or "Bike" in name_val or "Cycling" in name_val:
                name_val = f"{sport_val} Training"

        workouts.append({
            "day_offset": day_offset,
            "planned_date": workout_date.isoformat(),
            "name": name_val,
            "sport_type": sport_val,
            "duration_min": duration_val,
            "distance_m": dist_val,
            "intensity": intensity_val,
            "plan_metadata": meta_val,
        })

    return {
        "athlete_id": str(athlete_id),
        "start_date": start_date.isoformat(),
        "week_start_date": start_date.isoformat(),
        "duration_days": duration_days,
        "reasoning": ai_output.get("reasoning", "Adaptive progression based on recent volume and preferences."),
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

