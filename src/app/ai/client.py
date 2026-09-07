import os
import json
from typing import Dict, Any, List, Optional
import httpx

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


class ClaudeClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.model = "claude-3-5-sonnet-20241022"

    async def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        Calls Claude API and parses the structured JSON response.
        If no API key is provided, returns fallback simulated AI planning.
        """
        if not self.api_key:
            return self._fallback_response(user_prompt)

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "system": system_prompt + "\nYou must respond with valid raw JSON only, no markdown wrapping.",
            "messages": [
                {"role": "user", "content": user_prompt}
            ],
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(ANTHROPIC_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data["content"][0]["text"].strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            return json.loads(content.strip())

    def _fallback_response(self, user_prompt: str) -> Dict[str, Any]:
        """Deterministic simulation for tests and environments without live Anthropic API key."""
        return {
            "reasoning": "Progressive overload building aerobic base and recovery.",
            "workouts": [
                {
                    "day_offset": 0,
                    "name": "Base Endurance Ride",
                    "sport_type": "Ride",
                    "target_duration_min": 60,
                    "target_distance_m": 25000.0,
                    "target_intensity": 70.0,
                    "plan_metadata": {
                        "structure": {
                            "warmup": {"duration_min": 10, "description": "Easy spinning"},
                            "main_set": [{"intervals": 1, "duration_min": 40, "intensity": "Zone 2", "recovery_min": 0}],
                            "cooldown": {"duration_min": 10, "description": "Cool down spin"},
                        },
                        "target_duration_min": 60,
                        "target_intensity": "endurance",
                        "reasoning": "Building aerobic capacity",
                    },
                },
                {
                    "day_offset": 1,
                    "name": "Tempo Run",
                    "sport_type": "Run",
                    "target_duration_min": 45,
                    "target_distance_m": 8000.0,
                    "target_intensity": 85.0,
                    "plan_metadata": {
                        "structure": {
                            "warmup": {"duration_min": 10, "description": "Easy jog"},
                            "main_set": [{"intervals": 3, "duration_min": 8, "intensity": "tempo", "recovery_min": 2}],
                            "cooldown": {"duration_min": 5, "description": "Walking cool down"},
                        },
                        "target_duration_min": 45,
                        "target_intensity": "tempo",
                        "reasoning": "Lactate threshold stimulus",
                    },
                },
            ],
        }
