from typing import List, Any, Dict
import httpx
from datetime import datetime
from integrations.intervals_icu.mappers import map_icu_activity_to_completed
from models.completed_activity import CompletedActivity

BASE_URL = "https://intervals.icu/api/v1"

class IntervalsClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def get_activities_from_date(
        self,
        athlete_id: str,
        from_date: datetime
    ) -> List[CompletedActivity]:
        url = f"{BASE_URL}/athlete/{athlete_id}/activities"
        params = {"from": from_date.isoformat()}

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, auth=(self.api_key, ""), params=params)
            resp.raise_for_status()
            response: List[Dict[str, Any]] = resp.json()

        activities: List[CompletedActivity] = [
            map_icu_activity_to_completed(activity, athlete_id)
            for activity in response
        ]
        return activities
