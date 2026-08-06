# Expose router modules for direct access
# This allows: from app.api.routers import strava
from app.api.routers.athletes import router as athletes
from app.api.routers.completed_activities import router as completed_activities
from app.api.routers.planned_activities import router as planned_activities
from app.api.routers.activities import router as activities
from app.api.routers.strava import router as strava

__all__ = ["athletes", "completed_activities", "planned_activities", "activities", "strava"]