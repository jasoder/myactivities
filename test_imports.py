#!/usr/bin/env python3
"""Quick import verification script."""
import sys
sys.path.insert(0, '.')

print("Testing imports...")

try:
    from app.db.base import Base
    print("✓ db.base imports OK")

    from app.models.athlete import Athlete
    print("✓ models.athlete imports OK")

    from app.models.activities import Activity, WeekPlan, TrainingPreference
    print("✓ models.activities imports OK")

    from app.services.strava_sync_service import sync_athlete_activities
    print("✓ services.strava_sync_service imports OK")

    from app.api.routers.strava import router
    print("✓ api.routers.strava imports OK")

    from app.api.api_router import api_router
    print("✓ api.api_router imports OK")

    from app.main import app
    print("✓ app.main imports OK (FastAPI app created)")

    print("\n✅ All imports successful! The app should run cleanly.")

except Exception as e:
    print(f"\n❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)