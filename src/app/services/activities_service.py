import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.activities import Activity, ActivityMetric, ActivityStatus
from app.schemas.activities import (
    ActivitiesEntry,
    ActivitiesSummary,
    ActivityCreate,
    ActivityUpdate,
    ActivityMetricCreate,
)


def _build_activities_entry(
    *,
    id: uuid.UUID,
    date: datetime,
    title: str,
    type: str,
    status: str,
    distance_m: Optional[float],
    duration_s: Optional[int],
    training_load: Optional[float],
) -> ActivitiesEntry:
    """Factory function to build ActivitiesEntry with ActivitiesSummary."""
    return ActivitiesEntry(
        id=id,
        date=date,
        title=title or "Untitled Activity",
        type=type or "Other",
        status=status,
        data=ActivitiesSummary(
            distance_m=distance_m,
            duration_s=duration_s,
            training_load=training_load,
        ),
    )


async def get_activities_by_athlete(
    db: AsyncSession, athlete_id: uuid.UUID
) -> List[Activity]:
    result = await db.execute(
        select(Activity)
        .where(Activity.athlete_id == athlete_id)
        .options(selectinload(Activity.metrics))
    )
    return list(result.scalars().all())


async def get_activity_by_id(
    db: AsyncSession, activity_id: uuid.UUID
) -> Optional[Activity]:
    result = await db.execute(
        select(Activity)
        .where(Activity.id == activity_id)
        .options(selectinload(Activity.metrics))
    )
    return result.scalar_one_or_none()


async def get_activities_by_date_range(
    db: AsyncSession, athlete_id: uuid.UUID, start_date: datetime, end_date: datetime
) -> List[Activity]:
    # Query activities where planned_date or actual_date falls within [start_date, end_date]
    result = await db.execute(
        select(Activity)
        .where(
            Activity.athlete_id == athlete_id,
            or_(
                and_(
                    Activity.planned_date.isnot(None),
                    Activity.planned_date >= start_date,
                    Activity.planned_date <= end_date,
                ),
                and_(
                    Activity.actual_date.isnot(None),
                    Activity.actual_date >= start_date,
                    Activity.actual_date <= end_date,
                ),
            ),
        )
        .options(selectinload(Activity.metrics))
    )
    return list(result.scalars().all())


async def create_activity(
    db: AsyncSession,
    activity_in: ActivityCreate,
    metrics_in: Optional[ActivityMetricCreate] = None,
) -> Activity:
    new_activity = Activity(**activity_in.model_dump())
    if metrics_in and new_activity.status == ActivityStatus.completed:
        new_activity.metrics = ActivityMetric(**metrics_in.model_dump())
    db.add(new_activity)
    await db.commit()
    await db.refresh(new_activity)
    return new_activity


async def update_activity(
    db: AsyncSession,
    db_activity: Activity,
    activity_in: ActivityUpdate,
) -> Activity:
    update_data = activity_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_activity, field, value)

    await db.commit()
    await db.refresh(db_activity)
    return db_activity


async def delete_activity(db: AsyncSession, activity: Activity) -> None:
    await db.delete(activity)
    await db.commit()


async def get_activities_events(
    db: AsyncSession, athlete_id: uuid.UUID, start_date: datetime, end_date: datetime
) -> List[ActivitiesEntry]:
    activities = await get_activities_by_date_range(db, athlete_id, start_date, end_date)

    events: List[ActivitiesEntry] = []

    for a in activities:
        # Determine effective date
        date_val = a.actual_date if a.status == ActivityStatus.completed else a.planned_date
        if not date_val:
            date_val = a.planned_date or a.actual_date
        if not date_val:
            continue

        # Extract duration & distance from metrics if available, else from activity fields
        metrics = a.metrics
        distance = (
            metrics.distance_m
            if (metrics and metrics.distance_m is not None)
            else a.distance_m
        )
        duration_s = (
            (metrics.duration_min * 60)
            if (metrics and metrics.duration_min is not None)
            else (a.duration_min * 60 if a.duration_min is not None else None)
        )
        training_load = (
            metrics.icu_training_load
            if (metrics and metrics.icu_training_load is not None)
            else a.intensity
        )

        events.append(
            _build_activities_entry(
                id=a.id,
                date=date_val,
                title=a.name or "Untitled Activity",
                type=a.sport_type or "Other",
                status=a.status.value,
                distance_m=distance,
                duration_s=duration_s,
                training_load=training_load,
            )
        )

    events.sort(key=lambda x: x.date)
    return events

