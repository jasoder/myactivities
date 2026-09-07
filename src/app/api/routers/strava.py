import os
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from app.db.session import get_db
from app.models.athlete import Athlete
from app.integrations.strava.client import StravaClient
import uuid

router = APIRouter()


@router.get("/auth-url")
async def get_strava_auth_url(
    redirect_uri: str = Query(..., description="OAuth redirect URI")
):
    """Get Strava OAuth authorization URL."""
    client_id = os.getenv("STRAVA_CLIENT_ID")
    if not client_id:
        raise HTTPException(
            status_code=500, detail="STRAVA_CLIENT_ID environment variable not set"
        )
    return {"auth_url": StravaClient.get_authorization_url(client_id, redirect_uri)}


@router.post("/oauth/callback")
async def strava_oauth_callback(
    code: str = Query(..., description="Authorization code from Strava"),
    athlete_id: str = Query(..., description="Athlete ID"),
    db: AsyncSession = Depends(get_db),
):
    """Handle Strava OAuth callback and store tokens."""
    client_id = os.getenv("STRAVA_CLIENT_ID")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise HTTPException(
            status_code=500,
            detail="STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET environment variables not set",
        )

    try:
        token_data = await StravaClient.exchange_code_for_token(
            code, client_id, client_secret
        )

        async with StravaClient(token_data["access_token"]) as client:
            athlete_data = await client.get_athlete()

        result = await db.execute(select(Athlete).where(Athlete.id == athlete_id))
        athlete = result.scalar_one_or_none()
        if not athlete:
            raise HTTPException(status_code=404, detail="Athlete not found")

        athlete.strava_id = str(athlete_data["id"])
        athlete.access_token = token_data["access_token"]
        athlete.refresh_token = token_data.get("refresh_token")
        athlete.token_expires_at = datetime.fromtimestamp(
            token_data["expires_at"], tz=timezone.utc
        )

        await db.commit()

        return {
            "strava_id": athlete.strava_id,
            "athlete_name": athlete_data.get("firstname", "")
            + " "
            + athlete_data.get("lastname", ""),
            "connected": True,
        }
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"OAuth callback failed: {str(e)}"
        )

@router.post("/sync")
async def sync_strava_activities(
    athlete_id: str = Query(..., description="Athlete ID"),
    force: bool = Query(False, description="Force full sync ignoring last sync time"),
    limit: int = Query(50, description="Maximum number of activities to sync"),
    db: AsyncSession = Depends(get_db)
):
    """
    Sync Strava activities for an athlete.

    Called by frontend on calendar mount to refresh activities.
    If force=false (default), only syncs activities since last sync.
    If force=true, does a full sync of all activities.
    """
    try:
        # Import here to avoid circular imports
        from app.services.strava_sync_service import sync_athlete_activities

        result = await sync_athlete_activities(athlete_id, db, force=force, limit=limit)
        return {
            "message": "Sync completed",
            "processed": result.get("processed", 0),
            "new": result.get("new", 0),
            "skipped": result.get("skipped", 0),
            "last_synced_at": result.get("last_synced_at")
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/webhook")
async def strava_webhook_subscription(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
):
    """
    Strava Webhook subscription challenge verification.
    """
    expected_token = os.getenv("STRAVA_VERIFY_TOKEN", "STRAVA_WEBHOOK_VERIFY_TOKEN")
    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        return {"hub.challenge": hub_challenge}
    raise HTTPException(status_code=403, detail="Invalid verification token")


@router.post("/webhook")
async def strava_webhook_event(
    event: dict,
    db: AsyncSession = Depends(get_db),
):
    """
    Receive real-time push events from Strava and trigger activity sync.
    """
    object_type = event.get("object_type")
    aspect_type = event.get("aspect_type")
    owner_id = str(event.get("owner_id"))

    if object_type == "activity" and aspect_type in ["create", "update"]:
        # Find athlete by strava_id
        res = await db.execute(select(Athlete).where(Athlete.strava_id == owner_id))
        athlete = res.scalar_one_or_none()
        if athlete:
            from app.services.strava_sync_service import sync_athlete_activities
            await sync_athlete_activities(str(athlete.id), db, force=False, limit=5)

    return {"status": "ok"}