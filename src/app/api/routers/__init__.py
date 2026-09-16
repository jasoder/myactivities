# Expose router modules for direct access
# This allows: from app.api.routers import strava
from app.api.routers.athletes import router as athletes
from app.api.routers.activities import router as activities
from app.api.routers.strava import router as strava

__all__ = ["athletes", "activities", "strava"]