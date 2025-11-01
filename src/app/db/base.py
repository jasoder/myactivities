from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.models.athlete import Athlete
from app.models.completed_activity import CompletedActivity
from app.models.planned_activity import PlannedActivity

DATABASE_URL = "postgresql+asyncpg://postgres@localhost:8443/myactivities"

engine = create_async_engine(
    DATABASE_URL,
    echo=True
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

__all__ = ["Athlete", "CompletedActivity", "PlannedActivity", "Base", "engine", "async_session"]

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)