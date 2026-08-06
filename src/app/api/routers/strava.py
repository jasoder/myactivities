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

@router.post("/sync/latest/{athlete_id}")
async def sync_latest_strava_activity(athlete_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Sync the latest activity from Strava for an athlete."""
    try:
        result = await service.sync_strava_latest_activity(str(athlete_id), db)
        if result:
            return {"message": "Activity synced successfully", "activity": result}
        else:
            return {"message": "No new activities to sync"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))