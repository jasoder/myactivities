from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import uuid
from typing import Dict, Any

from app.db.session import get_db
from app.ai.planner_service import (
    generate_adaptive_week_plan,
    confirm_adaptive_week_plan,
    generate_weekly_recap,
)
from app.ai.load_analysis_service import calculate_athlete_training_load

router = APIRouter()


@router.get("/training-load/{athlete_id}")
async def get_training_load(
    athlete_id: uuid.UUID,
    days_back: int = Query(28, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """Calculate historical training load for athlete."""
    return await calculate_athlete_training_load(db, athlete_id, days_back=days_back)


@router.post("/generate-week-plan")
async def generate_week_plan_preview(
    athlete_id: uuid.UUID = Query(...),
    week_start: datetime = Query(..., description="Start date of the target week"),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate an AI adaptive weekly plan preview.
    The user can inspect and modify before confirming.
    """
    try:
        return await generate_adaptive_week_plan(db, athlete_id, week_start)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planning generation failed: {str(e)}")


@router.post("/confirm-week-plan", status_code=status.HTTP_201_CREATED)
async def confirm_week_plan_endpoint(
    plan_payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    """
    Confirm and write the AI generated week plan and scheduled activities to DB.
    """
    try:
        athlete_id = uuid.UUID(plan_payload["athlete_id"])
        week_plan = await confirm_adaptive_week_plan(db, athlete_id, plan_payload)
        return {"week_plan_id": str(week_plan.id), "status": week_plan.status}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to confirm plan: {str(e)}")


@router.get("/weekly-recap/{athlete_id}")
async def get_weekly_recap_endpoint(
    athlete_id: uuid.UUID,
    week_start: datetime = Query(..., description="Start date of the week to recap"),
    db: AsyncSession = Depends(get_db),
):
    """Generate weekly recap / morning report comparing planned vs completed."""
    return await generate_weekly_recap(db, athlete_id, week_start)
