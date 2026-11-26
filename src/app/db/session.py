from app.db.base import async_session


async def get_db():
    """FastAPI dependency yielding an async SQLAlchemy session."""
    async with async_session() as session:
        yield session
