# Expose router modules for direct access
from app.api.routers.activities import router as activities
from app.api.routers.strava import router as strava
from app.api.routers.ai import router as ai
from app.api.routers.auth import router as auth
from app.api.routers.user import router as user

__all__ = ["activities", "strava", "ai", "auth", "user"]