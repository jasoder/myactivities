from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import uuid
from typing import Dict, Any, Optional
from app.models.athlete import Athlete
from app.services.auth_service import get_optional_current_athlete
from app.db.session import get_db
from app.ai.planner_service import (
    generate_adaptive_plan,
    generate_adaptive_week_plan,
    confirm_adaptive_plan,
    confirm_adaptive_week_plan,
    generate_weekly_recap,
)
from app.ai.load_analysis_service import calculate_athlete_training_load
from app.schemas.activities import ConfirmPlanRequest, ConfirmWeekPlanRequest

router = APIRouter()


@router.get("/training-load")
@router.get("/training-load/{athlete_id}")
async def get_training_load(
    athlete_id: Optional[uuid.UUID] = None,
    days_back: int = Query(28, description="Number of days to analyze"),
    current_athlete: Optional[Athlete] = Depends(get_optional_current_athlete),
    db: AsyncSession = Depends(get_db),
):
    """Calculate historical training load for athlete."""
    target_athlete_id = athlete_id or (current_athlete.id if current_athlete else None)
    if not target_athlete_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="athlete_id parameter or Bearer authentication is required.",
        )
    return await calculate_athlete_training_load(db, target_athlete_id, days_back=days_back)


@router.post("/generate-plan")
async def generate_plan_preview(
    start_date: datetime = Query(..., description="Start date of the training plan"),
    athlete_id: Optional[uuid.UUID] = Query(None, description="Athlete ID (optional if authenticated)"),
    duration_days: int = Query(7, ge=1, le=60, description="Plan duration in days (e.g. 7 for 1 week, 28 for 1 month)"),
    current_athlete: Optional[Athlete] = Depends(get_optional_current_athlete),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate an AI adaptive training plan preview for an arbitrary duration (e.g., 7 days, 14 days, 28 days).
    The user can inspect and modify before confirming.
    """
    target_athlete_id = athlete_id or (current_athlete.id if current_athlete else None)
    if not target_athlete_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="athlete_id query parameter or Bearer authentication is required.",
        )
    try:
        return await generate_adaptive_plan(db, target_athlete_id, start_date=start_date, duration_days=duration_days)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planning generation failed: {str(e)}")


@router.post("/generate-week-plan")
async def generate_week_plan_preview(
    week_start: datetime = Query(..., description="Start date of the target week"),
    athlete_id: Optional[uuid.UUID] = Query(None, description="Athlete ID (optional if authenticated)"),
    current_athlete: Optional[Athlete] = Depends(get_optional_current_athlete),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate an AI adaptive weekly plan preview (7 days).
    The user can inspect and modify before confirming.
    """
    target_athlete_id = athlete_id or (current_athlete.id if current_athlete else None)
    if not target_athlete_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="athlete_id query parameter or Bearer authentication is required.",
        )
    try:
        return await generate_adaptive_week_plan(db, target_athlete_id, week_start)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planning generation failed: {str(e)}")


@router.post("/confirm-plan", status_code=status.HTTP_201_CREATED)
async def confirm_plan_endpoint(
    plan_payload: ConfirmPlanRequest,
    current_athlete: Optional[Athlete] = Depends(get_optional_current_athlete),
    db: AsyncSession = Depends(get_db),
):
    """
    Confirm and write the AI generated plan (arbitrary duration) and scheduled activities to DB.
    """
    target_athlete_id = plan_payload.athlete_id or (current_athlete.id if current_athlete else None)
    if not target_athlete_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="athlete_id in request body or Bearer authentication is required.",
        )
    try:
        payload_dict = plan_payload.model_dump(mode="json")
        payload_dict["athlete_id"] = str(target_athlete_id)
        plan = await confirm_adaptive_plan(db, target_athlete_id, payload_dict)
        return {"plan_id": str(plan.id), "week_plan_id": str(plan.id), "status": plan.status}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to confirm plan: {str(e)}")


@router.post("/confirm-week-plan", status_code=status.HTTP_201_CREATED)
async def confirm_week_plan_endpoint(
    plan_payload: ConfirmWeekPlanRequest,
    current_athlete: Optional[Athlete] = Depends(get_optional_current_athlete),
    db: AsyncSession = Depends(get_db),
):
    """
    Confirm and write the AI generated week plan and scheduled activities to DB.
    """
    target_athlete_id = plan_payload.athlete_id or (current_athlete.id if current_athlete else None)
    if not target_athlete_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="athlete_id in request body or Bearer authentication is required.",
        )
    try:
        payload_dict = plan_payload.model_dump(mode="json")
        payload_dict["athlete_id"] = str(target_athlete_id)
        week_plan = await confirm_adaptive_week_plan(db, target_athlete_id, payload_dict)
        return {"week_plan_id": str(week_plan.id), "status": week_plan.status}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to confirm plan: {str(e)}")


@router.get("/weekly-recap")
@router.get("/weekly-recap/{athlete_id}")
async def get_weekly_recap_endpoint(
    week_start: datetime = Query(..., description="Start date of the week to recap"),
    athlete_id: Optional[uuid.UUID] = None,
    duration_days: int = Query(7, ge=1, le=60, description="Duration in days to recap"),
    current_athlete: Optional[Athlete] = Depends(get_optional_current_athlete),
    db: AsyncSession = Depends(get_db),
):
    """Generate recap / morning report comparing planned vs completed activities."""
    target_athlete_id = athlete_id or (current_athlete.id if current_athlete else None)
    if not target_athlete_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="athlete_id parameter or Bearer authentication is required.",
        )
    return await generate_weekly_recap(db, target_athlete_id, week_start, duration_days=duration_days)


