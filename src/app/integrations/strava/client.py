import os
from typing import Dict, Any, Optional
import httpx
from datetime import datetime, timedelta

STRAVA_BASE_URL = "https://www.strava.com/api/v3"

class StravaClient:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.client = httpx.AsyncClient(
            base_url=STRAVA_BASE_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def get_athlete(self) -> Dict[str, Any]:
        """Get authenticated athlete details."""
        response = await self.client.get("/athlete")
        response.raise_for_status()
        return response.json()

    async def get_activities(self, before: Optional[datetime] = None, after: Optional[datetime] = None, page: int = 1, per_page: int = 30) -> list[Dict[str, Any]]:
        """Get list of activities."""
        params = {"page": page, "per_page": per_page}
        if before:
            params["before"] = int(before.timestamp())
        if after:
            params["after"] = int(after.timestamp())

        response = await self.client.get("/activities", params=params)
        response.raise_for_status()
        return response.json()

    async def get_activity(self, activity_id: str) -> Dict[str, Any]:
        """Get detailed activity by ID."""
        response = await self.client.get(f"/activities/{activity_id}")
        response.raise_for_status()
        return response.json()

    async def get_latest_activity(self) -> Optional[Dict[str, Any]]:
        """Get the most recent activity."""
        activities = await self.get_activities(page=1, per_page=1)
        return activities[0] if activities else None

    @staticmethod
    async def exchange_code_for_token(code: str, client_id: str, client_secret: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.strava.com/oauth/token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "grant_type": "authorization_code"
                }
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def refresh_access_token(refresh_token: str, client_id: str, client_secret: str) -> Dict[str, Any]:
        """Refresh access token using refresh token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.strava.com/oauth/token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token"
                }
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    def get_authorization_url(client_id: str, redirect_uri: str, scope: str = "read,activity:read") -> str:
        """Generate Strava authorization URL."""
        return (
            f"https://www.strava.com/oauth/authorize?"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"scope={scope}"
        )