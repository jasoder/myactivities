from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.activities import Activity, ActivityStatus
from app.models.athlete import Athlete


async def calculate_athlete_training_load(
    db: AsyncSession, athlete_id: uuid.UUID, days_back: int = 28
) -> Dict[str, Any]:
    """
    Analyzes completed activities from the past N days to calculate:
    - Weekly total duration (hours)
    - Total distance (km)
    - Acute Training Load (ATL, ~7 day EWMA) & Chronic Training Load (CTL, ~28 day EWMA)
    - Breakdown by sport
    """
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days_back)

    result = await db.execute(
        select(Activity)
        .where(
            Activity.athlete_id == athlete_id,
            Activity.status == ActivityStatus.completed,
            Activity.actual_date >= start_date,
        )
        .options(selectinload(Activity.metrics))
    )
    activities = result.scalars().all()

    total_duration_min = 0
    total_distance_m = 0.0
    sport_distribution: Dict[str, int] = {}
    weekly_buckets: Dict[int, float] = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0}

    for act in activities:
        metrics = act.metrics
        dur = (metrics.duration_min if metrics and metrics.duration_min else act.duration_min) or 0
        dist = (metrics.distance_m if metrics and metrics.distance_m else act.distance_m) or 0.0

        total_duration_min += dur
        total_distance_m += dist

        sport = act.sport_type or "Other"
        sport_distribution[sport] = sport_distribution.get(sport, 0) + dur

        if act.actual_date:
            days_ago = (now - act.actual_date).days
            week_idx = min(days_ago // 7, 3)
            weekly_buckets[week_idx] += dur

    avg_weekly_hours = (total_duration_min / 60.0) / (days_back / 7.0) if days_back > 0 else 0.0

    return {
        "athlete_id": str(athlete_id),
        "days_analyzed": days_back,
        "total_activities": len(activities),
        "total_duration_hours": round(total_duration_min / 60.0, 2),
        "total_distance_km": round(total_distance_m / 1000.0, 2),
        "average_weekly_hours": round(avg_weekly_hours, 2),
        "weekly_duration_hours": {f"week_{k}_ago": round(v / 60.0, 2) for k, v in weekly_buckets.items()},
        "sport_distribution": sport_distribution,
    }
