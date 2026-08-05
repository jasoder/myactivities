# Sync session for simple operations
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from .base import Base, async_session
import os


# Sync engine and session for compatibility
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:myactivities@localhost:5432/myactivities-test")
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoescape=False, bind=engine)

# Create tables if they don't exist (wrapped to prevent blocking startup)
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Warning: Could not create tables on import: {e}")

# Dependency for FastAPI routes
async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()