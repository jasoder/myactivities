import os
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.integrations.strava.client import StravaClient
from app.integrations.strava.mappers import map_strava_activity_to_completed
from app.models.athlete import Athlete
from app.models.completed_activity import CompletedActivity
from app.services.completed_activity_service import create_completed_activity
from app.schemas.completed_activity import CompletedActivityCreate

async def sync_strava_latest_activity(athlete_id: str, db: AsyncSession) -> Optional[dict]:
    """
    Fetch the latest activity from Strava and save it to the database.
    Returns the created activity data or None if no new activity.
    """
    # Get athlete with Strava tokens
    result = await db.execute(select(Athlete).where(Athlete.id == athlete_id))
    athlete = result.scalar_one_or_none()
    if not athlete or not athlete.access_token:
        raise ValueError("Athlete not found or no Strava access token")

    # Check if token is expired and refresh if needed
    if athlete.token_expires_at and athlete.token_expires_at <= datetime.now(timezone.utc):
        if not athlete.refresh_token:
            raise ValueError("Access token expired and no refresh token available")

        # Refresh token
        token_data = await StravaClient.refresh_access_token(
            athlete.refresh_token,
            os.getenv("STRAVA_CLIENT_ID"),
            os.getenv("STRAVA_CLIENT_SECRET")
        )

        # Update athlete with new tokens
        athlete.access_token = token_data["access_token"]
        athlete.refresh_token = token_data.get("refresh_token", athlete.refresh_token)
        athlete.token_expires_at = datetime.fromtimestamp(token_data["expires_at"], tz=timezone.utc)
        await db.commit()

    async with StravaClient(athlete.access_token) as client:
        # Get the latest activity
        strava_activity = await client.get_latest_activity()
        if not strava_activity:
            return None

        # Check if activity already exists
        result = await db.execute(
            select(CompletedActivity).where(
                CompletedActivity.strava_id == str(strava_activity["id"]),
                CompletedActivity.athlete_id == athlete_id
            )
        )
        existing_activity = result.scalar_one_or_none()
        if existing_activity:
            return None  # Activity already synced

        # Map to our model
        activity = map_strava_activity_to_completed(strava_activity, athlete_id)

        # Save to database
        db.add(activity)
        await db.commit()
        await db.refresh(activity)

        return {
            "id": activity.id,
            "name": activity.name,
            "sport_type": activity.sport_type,
            "start_date_local": activity.start_date_local,
            "distance_m": activity.distance_m,
            "moving_time_s": activity.moving_time_s
        }

async def get_strava_authorization_url(redirect_uri: str) -> str:
    """Generate Strava OAuth authorization URL."""
    client_id = os.getenv("STRAVA_CLIENT_ID")
    if not client_id:
        raise ValueError("STRAVA_CLIENT_ID environment variable not set")

    return StravaClient.get_authorization_url(client_id, redirect_uri)

async def handle_strava_oauth_callback(code: str, athlete_id: str, db: AsyncSession) -> dict:
    """Handle OAuth callback and store tokens."""
    client_id = os.getenv("STRAVA_CLIENT_ID")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError("STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET environment variables not set")

    # Exchange code for tokens
    token_data = await StravaClient.exchange_code_for_token(code, client_id, client_secret)

    # Get athlete details
    async with StravaClient(token_data["access_token"]) as client:
        athlete_data = await client.get_athlete()

    # Update athlete with Strava data and tokens
    result = await db.execute(select(Athlete).where(Athlete.id == athlete_id))
    athlete = result.scalar_one_or_none()
    if not athlete:
        raise ValueError("Athlete not found")

    athlete.strava_id = str(athlete_data["id"])
    athlete.access_token = token_data["access_token"]
    athlete.refresh_token = token_data.get("refresh_token")
    athlete.token_expires_at = datetime.fromtimestamp(token_data["expires_at"], tz=timezone.utc)

    await db.commit()

    return {
        "strava_id": athlete.strava_id,
        "athlete_name": athlete_data.get("firstname", "") + " " + athlete_data.get("lastname", ""),
        "connected": True
    }