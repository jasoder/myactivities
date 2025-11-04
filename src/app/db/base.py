from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "postgresql+asyncpg://postgres@localhost:8443/myactivities"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass

from app.models.athlete import Athlete 
from app.models.completed_activity import CompletedActivity
from app.models.planned_activity import PlannedActivity

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)