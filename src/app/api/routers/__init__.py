from app.api.routers.athletes import router as athletes_router
from app.api.routers.completed_activities import router as completed_activities_router
from app.api.routers.planned_activities import router as planned_activities_router
from app.api.routers.activities import router as activities_router
from app.api.routers.strava import router as strava_router

__all__ = [
    "athletes_router",
    "completed_activities_router",
    "planned_activities_router",
    "activities_router",
    "strava_router",
]
