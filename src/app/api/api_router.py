from fastapi import APIRouter
from starlette.responses import JSONResponse
from app.schemas.errors import ErrorResponse
from app.api.routers import athletes, completed_activities, planned_activities, activities

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

api_router.include_router(athletes.router, prefix="/athletes", tags=["Athletes"])
api_router.include_router(completed_activities.router, prefix="/completedActivities", tags=["Completed Activities"])
api_router.include_router(planned_activities.router, prefix="/plannedActivities", tags=["Planned Activities"])
api_router.include_router(activities.router, prefix="/activities", tags=["Activities"])
