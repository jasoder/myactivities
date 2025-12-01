import asyncio
from app.db.base import Base, engine

# Import models here so SQLAlchemy knows about them
from app.models import athlete, completed_activity, planned_activity

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database initialized successfully")

if __name__ == "__main__":
    asyncio.run(init_db())