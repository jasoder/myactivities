import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import async_session
from app.models.athlete import Athlete
from app.models.activities import Activity, ActivityMetric, ActivityStatus
from app.enums import ActivitySource

# python3 src/scripts/seed_db.py

async def seed_db():
    async with async_session() as session:
        # Create athlete
        athlete_id = uuid.uuid4()
        athlete = Athlete(
            id=athlete_id,
            name="Test Athlete",
            email="test@example.com"
        )
        session.add(athlete)
        await session.flush()
        
        # Create 2 completed activities in January
        act1 = Activity(
            id=uuid.uuid4(),
            athlete_id=athlete_id,
            name="Morning Ride",
            source=ActivitySource.STRAVA,
            status=ActivityStatus.completed,
            sport_type="Ride",
            actual_date=datetime(2026, 1, 3, 8, 0, 0, tzinfo=timezone.utc),
            distance_m=32000.0,
            duration_min=60,
            metrics=ActivityMetric(
                distance_m=32000.0,
                duration_min=60,
                icu_training_load=85.5,
            )
        )
        
        act2 = Activity(
            id=uuid.uuid4(),
            athlete_id=athlete_id,
            name="Evening Run",
            source=ActivitySource.STRAVA,
            status=ActivityStatus.completed,
            sport_type="Run",
            actual_date=datetime(2026, 1, 5, 17, 0, 0, tzinfo=timezone.utc),
            distance_m=10000.0,
            duration_min=45,
            metrics=ActivityMetric(
                distance_m=10000.0,
                duration_min=45,
                icu_training_load=65.0,
            )
        )
        
        session.add(act1)
        session.add(act2)
        await session.flush()
        
        # Create 2 planned activities in January
        planned1 = Activity(
            id=uuid.uuid4(),
            athlete_id=athlete_id,
            name="Long Ride",
            source=ActivitySource.manual,
            status=ActivityStatus.planned,
            sport_type="Ride",
            planned_date=datetime(2026, 1, 12, 9, 0, 0, tzinfo=timezone.utc),
            distance_m=48000.0,
            duration_min=90,
            intensity=120.0,
        )
        
        planned2 = Activity(
            id=uuid.uuid4(),
            athlete_id=athlete_id,
            name="Interval Training",
            source=ActivitySource.manual,
            status=ActivityStatus.planned,
            sport_type="Run",
            planned_date=datetime(2026, 1, 18, 10, 0, 0, tzinfo=timezone.utc),
            distance_m=15000.0,
            duration_min=60,
            intensity=150.0,
        )
        
        session.add(planned1)
        session.add(planned2)
        
        await session.commit()
        print(f"Created athlete '{athlete.name}' (ID: {athlete_id})")
        print(f"Added 2 completed activities and 2 planned activities for January 2026")

if __name__ == "__main__":
    asyncio.run(seed_db())
