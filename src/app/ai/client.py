import os
import json
from typing import Dict, Any, List, Optional
import httpx


class AIClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("AI_API_KEY", "")
        self.api_url = api_url or os.getenv("AI_API_URL", "")
        self.model = model or os.getenv("AI_MODEL", "")

    async def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        if not self.api_url and not self.api_key:
            return self._fallback_response(user_prompt)

        target_url = self.api_url or "https://api.anthropic.com/v1/messages"
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        is_anthropic = "anthropic.com" in target_url or target_url.endswith("/messages")

        async with httpx.AsyncClient(timeout=45.0) as client:
            if is_anthropic:
                if self.api_key:
                    headers["x-api-key"] = self.api_key
                headers["anthropic-version"] = "2023-06-01"
                payload: Dict[str, Any] = {
                    "model": self.model or "claude-3-5-sonnet-20241022",
                    "max_tokens": 4096,
                    "system": system_prompt + "\nYou must respond with valid raw JSON only, no markdown wrapping.",
                    "messages": [{"role": "user", "content": user_prompt}],
                }
                response = await client.post(target_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                content = data["content"][0]["text"].strip()
            else:
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                endpoint = target_url
                if endpoint.endswith("/v1") or endpoint.endswith("/v1/"):
                    endpoint = f"{endpoint.rstrip('/')}/chat/completions"

                payload = {
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompt + "\nYou must respond with valid raw JSON only, no markdown formatting.",
                        },
                        {"role": "user", "content": user_prompt},
                    ],
                }
                if self.model:
                    payload["model"] = self.model

                response = await client.post(endpoint, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()

            return self._parse_json(content)

    def _parse_json(self, text: str) -> Dict[str, Any]:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            return json.loads(text)
        except Exception:
            pass

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            sub = text[start : end + 1]
            try:
                return json.loads(sub)
            except Exception:
                import re
                cleaned = re.sub(r",\s*([\]}])", r"\1", sub)
                try:
                    return json.loads(cleaned)
                except Exception:
                    pass
        raise ValueError(f"Failed to parse structured JSON from AI response: {text[:150]}")


    def _fallback_response(self, user_prompt: str) -> Dict[str, Any]:
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


