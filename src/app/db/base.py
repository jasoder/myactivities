from sqlalchemy.orm import DeclarativeBase
from app.models.athlete import Athlete
from app.models.completedActivity import CompletedActivity
from app.models.plannedActivity import PlannedActivity


__all__ = ["Athlete", "CompletedActivity", "PlannedActivity"]

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass