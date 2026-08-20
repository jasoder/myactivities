from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.integrations.strava import service
import uuid

router = APIRouter()

@router.get("/auth-url")
async def get_strava_auth_url(redirect_uri: str = Query(..., description="OAuth redirect URI")):
    """Get Strava OAuth authorization URL."""
    try:
        return {"auth_url": await service.get_strava_authorization_url(redirect_uri)}
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/oauth/callback")
async def strava_oauth_callback(
    code: str = Query(..., description="Authorization code from Strava"),
    athlete_id: str = Query(..., description="Athlete ID"),
    db: AsyncSession = Depends(get_db)
):
    """Handle Strava OAuth callback and store tokens."""
    try:
        result = await service.handle_strava_oauth_callback(code, athlete_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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