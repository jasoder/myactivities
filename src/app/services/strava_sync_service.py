"""
Strava sync service - implements Phase 2 requirements.
Syncs Strava activities on app open and upserts into the activities table.
"""

import os
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError

from app.models.athlete import Athlete
from app.models.activities import Activity, ActivityStatus
from app.enums import ActivitySource
from app.integrations.strava.client import StravaClient


async def sync_athlete_activities(
    athlete_id: str,
    db: AsyncSession,
    force: bool = False,
    limit: int = 50
) -> Dict[str, int]:
    """
    Sync Strava activities for an athlete.

    This is a key endpoint called by the frontend on calendar mount.
    It fetches activities from Strava and upserts them into the activities table.

    Args:
        athlete_id: UUID of the athlete
        db: Database session
        force: Force full sync (ignore last_synced_at)
        limit: Maximum number of activities to sync

    Returns:
        Dict with counts: {'processed': int, 'new': int, 'skipped': int}
    """
    # Get athlete record
    result = await db.execute(select(Athlete).where(Athlete.id == athlete_id))
    athlete = result.scalar_one_or_none()

    if not athlete:
        raise ValueError(f"Athlete {athlete_id} not found")

    # Check if Strava is connected
    if not athlete.access_token:
        raise ValueError(f"Athlete {athlete_id} has no Strava access token")

    # Refresh token if expired
    if athlete.token_expires_at and athlete.token_expires_at <= datetime.now(timezone.utc) + timedelta(minutes=5):
        if not athlete.refresh_token:
            raise ValueError("Access token expired and no refresh token available")

        token_data = await StravaClient.refresh_access_token(
            athlete.refresh_token,
            os.getenv("STRAVA_CLIENT_ID"),
            os.getenv("STRAVA_CLIENT_SECRET")
        )

        athlete.access_token = token_data["access_token"]
        athlete.refresh_token = token_data.get("refresh_token", athlete.refresh_token)
        athlete.token_expires_at = datetime.fromtimestamp(
            token_data["expires_at"], tz=timezone.utc
        )
        await db.commit()

    # Determine sync window
    after = athlete.last_synced_at if not force else datetime(2020, 1, 1, tzinfo=timezone.utc)

    # Create Strava client and fetch activities
    strava_client = StravaClient(athlete.access_token)

    processed = 0
    new_count = 0
    skipped = 0

    try:
        activities_data = await strava_client.get_activities(
            after=after,
            per_page=min(limit, 100)  # Strava max is 100 per page
        )

        for activity_data in activities_data:
            activity = await _upsert_strava_activity(
                db, athlete_id, activity_data
            )

            if activity:
                new_count += 1
            else:
                skipped += 1
            processed += 1

    finally:
        await strava_client.client.aclose()

    # Update last synced timestamp
    athlete.last_synced_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        'processed': processed,
        'new': new_count,
        'skipped': skipped,
        'last_synced_at': athlete.last_synced_at.isoformat()
    }


async def _upsert_strava_activity(
    db: AsyncSession,
    athlete_id: str,
    activity_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Upsert a Strava activity into the unified activities table.

    Returns the activity data if created, None if skipped (already exists).
    """
    strava_id = str(activity_data.get("id"))

    # Check if already exists (enforced by unique constraint on strava_activity_id)
    existing = await db.execute(
        select(Activity).where(
            Activity.strava_activity_id == strava_id,
            Activity.athlete_id == athlete_id
        )
    )
    if existing.scalar_one_or_none():
        return None

    # Map Strava data to Activity model
    start_date = activity_data.get("start_date_local") or activity_data.get("start_date")
    if isinstance(start_date, str):
        start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))

    activity = Activity(
        athlete_id=athlete_id,
        strava_activity_id=strava_id,
        external_id=activity_data.get("external_id"),
        source=ActivitySource.strava,
        status=ActivityStatus.completed,
        name=activity_data.get("name"),
        sport_type=_map_strava_sport_type(activity_data.get("type", "").lower()),
        description=activity_data.get("description"),
        duration_min=activity_data.get("duration") // 60 if activity_data.get("duration") else None,
        distance_m=activity_data.get("distance") * 1000 if activity_data.get("distance") else None,
        actual_date=start_date,
        plan_metadata={
            'calories': activity_data.get("calories"),
            'elevation_gain': activity_data.get("elevation_gain"),
        },
        last_sync=datetime.now(timezone.utc),
    )

    db.add(activity)
    await db.flush()  # Flush to get the ID

    return {
        'id': str(activity.id),
        'strava_activity_id': strava_id,
        'name': activity.name,
        'sport_type': activity.sport_type,
    }


def _map_strava_sport_type(strava_type: str) -> str:
    """Map Strava activity types to app sport types."""
    mapping = {
        'run': 'run',
        'ride': 'ride',
        'swim': 'swim',
        'virtual_ride': 'ride',
        'virtual_run': 'run',
        'weight_training': 'strength',
        'yoga': 'yoga',
        'strength_training': 'strength',
        'hike': 'hike',
        'walk': 'walk',
        'workout': 'strength',
        'crossfit': 'strength',
        'olympic_lifting': 'strength',
        'row': 'row',
        'kayak': 'water_sports',
        'stand_up_paddling': 'water_sports',
    }
    return mapping.get(strava_type, strava_type.replace('_', ' '))


async def sync_all_athlete_activities(
    athlete_id: str,
    db: AsyncSession,
    days_back: int = 365
) -> Dict[str, Any]:
    """
    Full sync for an athlete - fetches all activities within date range.
    Used when Strava connection is first established or data might be missing.
    """
    from datetime import timedelta

    before = datetime.now(timezone.utc)
    after = before - timedelta(days=days_back)

    strava_client = StravaClient((await db.execute(
        select(Athlete.access_token).where(Athlete.id == athlete_id)
    )).scalar_one_or_none())

    all_activities = []
    page = 1

    while True:
        activities = await strava_client.get_activities(
            before=before,
            after=after,
            page=page,
            per_page=100
        )

        if not activities:
            break

        all_activities.extend(activities)
        page += 1

    await strava_client.client.aclose()

    results = {'processed': 0, 'new': 0, 'skipped': 0}

    for activity_data in all_activities:
        result = await _upsert_strava_activity(db, athlete_id, activity_data)
        if result:
            results['new'] += 1
        else:
            results['skipped'] += 1
        results['processed'] += 1

    return results