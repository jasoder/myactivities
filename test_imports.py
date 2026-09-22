#!/usr/bin/env python3
"""Quick import verification script."""
import sys
sys.path.insert(0, '.')

print("Testing imports...")

try:
    from app.db.base import Base
    print("OK: db.base imports")

    from app.models.athlete import Athlete
    print("OK: models.athlete imports")

    from app.models.activities import Activity, WeekPlan, TrainingPreference
    print("OK: models.activities imports")

    from app.services.strava_sync_service import sync_athlete_activities
    print("OK: services.strava_sync_service imports")

    from app.api.routers.strava import router
    print("OK: api.routers.strava imports")

    from app.api.api_router import api_router
    print("OK: api.api_router imports")

    from app.main import app
    print("OK: app.main imports (FastAPI app created)")

    print("\nSUCCESS: All imports successful! The app should run cleanly.")

except Exception as e:
    print(f"\nERROR: Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)