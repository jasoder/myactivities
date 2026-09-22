from fastapi import APIRouter
from starlette.responses import JSONResponse
from app.schemas.errors import ErrorResponse
from app.api.routers.activities import router as activities
from app.api.routers.strava import router as strava
from app.api.routers.ai import router as ai
from app.api.routers.auth import router as auth
from app.api.routers.user import router as user

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

api_router.include_router(auth, prefix="/auth", tags=["Authentication"])
api_router.include_router(user, prefix="/user", tags=["User (Self)"])
api_router.include_router(activities, prefix="/activities", tags=["Activities"])
api_router.include_router(strava, prefix="/strava", tags=["Strava Integration"])
api_router.include_router(ai, prefix="/ai", tags=["AI Adaptive Scheduling"])
