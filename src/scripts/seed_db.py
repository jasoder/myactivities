import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import async_session
from app.models.athlete import Athlete
from app.models.completed_activity import CompletedActivity
from app.models.planned_activity import PlannedActivity
from app.enums import ActivityType, ActivityGoal, ActivitySource

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
        
        # Current month is January 2026
        now = datetime(2026, 1, 6, 12, 0, 0, tzinfo=timezone.utc)
        
        # Create 2 completed activities in January
        completed1 = CompletedActivity(
            id=uuid.uuid4(),
            athlete_id=athlete_id,
            name="Morning Ride",
            source=ActivitySource.STRAVA,
            sport_type="Ride",
            start_date=datetime(2026, 1, 3, 8, 0, 0, tzinfo=timezone.utc),
            start_date_local=datetime(2026, 1, 3, 8, 0, 0),
            distance_m=32000.0,
            moving_time_s=3600,
            icu_training_load=85.5
        )
        
        completed2 = CompletedActivity(
            id=uuid.uuid4(),
            athlete_id=athlete_id,
            name="Evening Run",
            source=ActivitySource.STRAVA,
            sport_type="Run",
            start_date=datetime(2026, 1, 5, 17, 0, 0, tzinfo=timezone.utc),
            start_date_local=datetime(2026, 1, 5, 17, 0, 0),
            distance_m=10000.0,
            moving_time_s=2700,
            icu_training_load=65.0
        )
        
        session.add(completed1)
        session.add(completed2)
        await session.flush()
        
        # Create 2 planned activities in January
        planned1 = PlannedActivity(
            id=uuid.uuid4(),
            athlete_id=athlete_id,
            name="Long Ride",
            type=ActivityType.ride,
            goal=ActivityGoal.endurance,
            scheduled_date=datetime(2026, 1, 12, 9, 0, 0, tzinfo=timezone.utc),
            target_distance=48000.0,
            target_duration=5400,
            target_intensity=120.0,
            completed=False
        )
        
        planned2 = PlannedActivity(
            id=uuid.uuid4(),
            athlete_id=athlete_id,
            name="Interval Training",
            type=ActivityType.run,
            goal=ActivityGoal.threshold,
            scheduled_date=datetime(2026, 1, 18, 10, 0, 0, tzinfo=timezone.utc),
            target_distance=15000.0,
            target_duration=3600,
            target_intensity=150.0,
            completed=False
        )
        
        session.add(planned1)
        session.add(planned2)
        
        await session.commit()
        print(f"Created athlete '{athlete.name}' (ID: {athlete_id})")
        print(f"Added 2 completed activities and 2 planned activities for January 2026")

if __name__ == "__main__":
    asyncio.run(seed_db())
