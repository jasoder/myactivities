from fastapi import APIRouter
from pydantic import BaseModel
from starlette.responses import JSONResponse
from app.api.routes import athletes, completed_activities, planned_activities

class ErrorMessage(BaseModel):
    """Represents a single error message."""

    msg: str


class ErrorResponse(BaseModel):
    """Defines the structure for API error responses."""

    detail: list[ErrorMessage] | None = None
    
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
api_router.include_router(completed_activities.router, prefix="/completedworkouts", tags=["Completed Workouts"])
api_router.include_router(planned_activities.router, prefix="/plannedworkouts", tags=["Planned Workouts"])
