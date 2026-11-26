import sys
from pathlib import Path
import uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.main import app
from app.db.session import get_db
from app.models.athlete import Athlete


@asynccontextmanager
async def mock_app():
    """Async context manager providing an HTTPX test client with mocked DB."""
    mock_db = AsyncMock()

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client
    finally:
        app.dependency_overrides.clear()


def mock_obj(**kwargs):
    """Create a MagicMock with given attributes."""
    obj = MagicMock()
    for k, v in kwargs.items():
        setattr(obj, k, v)
    return obj


def make_mock_athlete(
    athlete_id=None,
    email="user@example.com",
    name="Test User",
    hashed_pwd=None,
    ftp=None,
    threshold_pace=None,
    weight=None,
    max_hr=None,
    lthr=None,
    preferred_sports=None,
    timezone_str="UTC",
    weekly_training_hours=None,
):
    athlete = MagicMock(spec=Athlete)
    athlete.id = athlete_id or uuid.uuid4()
    athlete.email = email
    athlete.name = name
    athlete.hashed_password = hashed_pwd
    athlete.ftp = ftp
    athlete.threshold_pace = threshold_pace
    athlete.weight = weight
    athlete.max_hr = max_hr
    athlete.lthr = lthr
    athlete.strava_id = None
    athlete.access_token = None
    athlete.refresh_token = None
    athlete.token_expires_at = None
    athlete.strava_connected = False
    athlete.preferred_sports = preferred_sports if preferred_sports is not None else []
    athlete.timezone = timezone_str
    athlete.weekly_training_hours = weekly_training_hours
    athlete.ai_enabled = True
    athlete.created_at = datetime.now(timezone.utc)
    athlete.updated_at = datetime.now(timezone.utc)
    return athlete
