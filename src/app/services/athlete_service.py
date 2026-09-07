import uuid
from sqlalchemy import select, delete, exists
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.athlete import Athlete
from app.schemas.athlete import AthleteCreate, AthleteUpdate

async def get_athlete_by_id(db: AsyncSession, athlete_id: uuid.UUID) -> Athlete | None:
    result = await db.execute(select(Athlete).where(Athlete.id == athlete_id))
    
    return result.scalar_one_or_none()

async def create_new_athlete(db: AsyncSession, athlete_in: AthleteCreate) -> Athlete:
    new_athlete = Athlete(**athlete_in.model_dump())
    db.add(new_athlete)
    
    await db.commit()
    await db.refresh(new_athlete)
    
    return new_athlete

async def update_existing_athlete(db: AsyncSession, athlete: Athlete, athlete_in: AthleteUpdate) -> Athlete:
    for field, value in athlete_in.model_dump(exclude_unset=True).items():
        setattr(athlete, field, value)
    
    await db.commit()
    await db.refresh(athlete)
    
    return athlete

async def handle_strava_oauth_callback(
    db: AsyncSession, athlete_id: uuid.UUID, code: str
) -> dict:
    import os
    from datetime import datetime, timezone
    from app.integrations.strava.client import StravaClient

    client_id = os.getenv("STRAVA_CLIENT_ID")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise ValueError("STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET environment variables not set")

    token_data = await StravaClient.exchange_code_for_token(code, client_id, client_secret)

    async with StravaClient(token_data["access_token"]) as client:
        athlete_data = await client.get_athlete()

    athlete = await get_athlete_by_id(db, athlete_id)
    if not athlete:
        raise ValueError("Athlete not found")

    athlete.strava_id = str(athlete_data["id"])
    athlete.access_token = token_data["access_token"]
    athlete.refresh_token = token_data.get("refresh_token")
    athlete.token_expires_at = datetime.fromtimestamp(token_data["expires_at"], tz=timezone.utc)

    await db.commit()
    await db.refresh(athlete)

    return {
        "strava_id": athlete.strava_id,
        "athlete_name": athlete_data.get("firstname", "") + " " + athlete_data.get("lastname", ""),
        "connected": True,
    }