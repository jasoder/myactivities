from fastapi import APIRouter
from starlette.responses import JSONResponse
from app.schemas.errors import ErrorResponse
from app.api.routers.athletes import router as athletes
from app.api.routers.activities import router as activities
from app.api.routers.strava import router as strava

api_router = APIRouter(
    default_response_class=JSONResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)

api_router.include_router(athletes, prefix="/athletes", tags=["Athletes"])
api_router.include_router(activities, prefix="/activities", tags=["Activities"])
api_router.include_router(strava, prefix="/strava", tags=["Strava Integration"])
