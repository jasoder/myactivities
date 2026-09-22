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


async def delete_athlete_by_id(db: AsyncSession, athlete_id: uuid.UUID) -> bool:
    stmt = select(exists().where(Athlete.id == athlete_id))
    result = await db.execute(stmt)
    if not result.scalar():
        return False

    await db.execute(delete(Athlete).where(Athlete.id == athlete_id))
    await db.commit()
    return True


async def get_or_create_training_preferences(db: AsyncSession, athlete_id: uuid.UUID):
    from app.models.activities import TrainingPreference
    result = await db.execute(select(TrainingPreference).where(TrainingPreference.athlete_id == athlete_id))
    pref = result.scalar_one_or_none()
    if not pref:
        pref = TrainingPreference(athlete_id=athlete_id)
        db.add(pref)
        await db.commit()
        await db.refresh(pref)
    return pref


async def update_training_preferences(
    db: AsyncSession, athlete_id: uuid.UUID, pref_in
):
    pref = await get_or_create_training_preferences(db, athlete_id)
    for field, value in pref_in.model_dump(exclude_unset=True).items():
        setattr(pref, field, value)
    await db.commit()
    await db.refresh(pref)
    return pref

async def handle_strava_oauth_callback(
    db: AsyncSession, athlete_id: uuid.UUID | None, code: str
) -> dict:
    import os
    from datetime import datetime, timezone
    from app.integrations.strava.client import StravaClient
    from app.core.security import create_access_token

    client_id = os.getenv("STRAVA_CLIENT_ID")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise ValueError("STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET environment variables not set")

    token_data = await StravaClient.exchange_code_for_token(code, client_id, client_secret)

    async with StravaClient(token_data["access_token"]) as client:
        athlete_data = await client.get_athlete()

    strava_id_str = str(athlete_data["id"])
    strava_name = (athlete_data.get("firstname", "") + " " + athlete_data.get("lastname", "")).strip() or None

    if athlete_id:
        athlete = await get_athlete_by_id(db, athlete_id)
        if not athlete:
            raise ValueError("Athlete not found")
    else:
        # Check if athlete already connected with this Strava ID
        result = await db.execute(select(Athlete).where(Athlete.strava_id == strava_id_str))
        athlete = result.scalar_one_or_none()

        if not athlete:
            email = athlete_data.get("email") or f"strava_{strava_id_str}@myactivities.local"
            # Check if athlete with email exists
            existing_email = await db.execute(select(Athlete).where(Athlete.email == email))
            athlete = existing_email.scalar_one_or_none()

            if not athlete:
                athlete = Athlete(
                    email=email,
                    name=strava_name,
                )
                db.add(athlete)

    from app.core.security import create_access_token, ACCESS_TOKEN_EXPIRE_SECONDS

    athlete.strava_id = strava_id_str
    athlete.access_token = token_data["access_token"]
    athlete.refresh_token = token_data.get("refresh_token")
    athlete.token_expires_at = datetime.fromtimestamp(token_data["expires_at"], tz=timezone.utc)
    if not athlete.name and strava_name:
        athlete.name = strava_name

    await db.commit()
    await db.refresh(athlete)

    jwt_token = create_access_token({"sub": str(athlete.id), "email": athlete.email})

    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_SECONDS,
        "athlete_id": str(athlete.id),
        "email": athlete.email,
        "strava_id": athlete.strava_id,
        "athlete_name": strava_name or athlete.name or "",
        "connected": True,
        "strava_connected": True,
    }


async def disconnect_strava(db: AsyncSession, athlete: Athlete) -> Athlete:
    athlete.strava_id = None
    athlete.access_token = None
    athlete.refresh_token = None
    athlete.token_expires_at = None
    await db.commit()
    await db.refresh(athlete)
    return athlete