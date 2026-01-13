from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.services import planned_activity_service, completed_activity_service
from app.schemas.activities import ActivitiesEntry, ActivitiesSummary


async def get_activities_events(
    db: AsyncSession, athlete_id, start_date: datetime, end_date: datetime
):
    planned = await planned_activity_service.get_planned_activities_by_date_range(
        db, athlete_id, start_date, end_date
    )
    completed = await completed_activity_service.get_completed_activities_by_date_range(
        db, athlete_id, start_date, end_date
    )

    events = []

    for p in planned:
        status = "completed" if p.completed else "planned"
        events.append(
            ActivitiesEntry(
                id=p.id,
                date=p.scheduled_date,
                title=p.name,
                type=p.type,
                status=status,
                data=ActivitiesSummary(
                    distance_m=p.target_distance,
                    duration_s=p.target_duration,
                    training_load=p.target_intensity,
                ),
            )
        )

    for c in completed:
        date_val = c.start_date_local or c.start_date
        if date_val is None:
            continue
        events.append(
            ActivitiesEntry(
                id=c.id,
                date=date_val,
                title=c.name,
                type=c.sport_type,
                status="completed",
                data=ActivitiesSummary(
                    distance_m=c.distance_m,
                    duration_s=c.moving_time_s,
                    training_load=c.icu_training_load,
                ),
            )
        )

    events.sort(key=lambda x: x.date)
    return events
