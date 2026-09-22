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
        self.api_key = os.getenv("AI_API_KEY", "") if api_key is None else api_key
        self.api_url = os.getenv("AI_API_URL", "") if api_url is None else api_url
        self.model = os.getenv("AI_MODEL", "") if model is None else model

    async def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        if not self.api_url:
            return self._fallback_response(user_prompt)

        target_url = self.api_url
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        is_anthropic = "anthropic.com" in target_url or target_url.endswith("/messages")

        async with httpx.AsyncClient(timeout=45.0) as client:
            if is_anthropic:
                if self.api_key:
                    headers["x-api-key"] = self.api_key
                headers["anthropic-version"] = "2023-06-01"
                payload: Dict[str, Any] = {
                    "model": self.model,
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
        import re
        duration = 7
        match = re.search(r"(\d+)-day", user_prompt)
        if match:
            duration = int(match.group(1))
        else:
            match = re.search(r"Duration:\s*(\d+)", user_prompt)
            if match:
                duration = int(match.group(1))

        templates = [
            {
                "name": "Base Endurance Ride",
                "sport_type": "Ride",
                "target_duration_min": 60,
                "target_distance_m": 25000.0,
                "target_intensity": 70.0,
                "structure": {
                    "warmup": {"duration_min": 10, "description": "Easy spinning"},
                    "main_set": [{"intervals": 1, "duration_min": 40, "intensity": "Zone 2", "recovery_min": 0}],
                    "cooldown": {"duration_min": 10, "description": "Cool down spin"},
                },
                "reasoning": "Building aerobic capacity",
            },
            {
                "name": "Tempo Run",
                "sport_type": "Run",
                "target_duration_min": 45,
                "target_distance_m": 8000.0,
                "target_intensity": 85.0,
                "structure": {
                    "warmup": {"duration_min": 10, "description": "Easy jog"},
                    "main_set": [{"intervals": 3, "duration_min": 8, "intensity": "tempo", "recovery_min": 2}],
                    "cooldown": {"duration_min": 5, "description": "Walking cool down"},
                },
                "reasoning": "Lactate threshold stimulus",
            },
            {
                "name": "Active Recovery & Mobility",
                "sport_type": "Other",
                "target_duration_min": 30,
                "target_distance_m": 0.0,
                "target_intensity": 50.0,
                "structure": {
                    "warmup": {"duration_min": 5, "description": "Dynamic stretching"},
                    "main_set": [{"intervals": 1, "duration_min": 20, "intensity": "mobility & core", "recovery_min": 0}],
                    "cooldown": {"duration_min": 5, "description": "Static stretch"},
                },
                "reasoning": "Promote recovery and soft tissue health",
            },
            {
                "name": "VO2 Max Interval Ride",
                "sport_type": "Ride",
                "target_duration_min": 50,
                "target_distance_m": 22000.0,
                "target_intensity": 90.0,
                "structure": {
                    "warmup": {"duration_min": 15, "description": "Progressive warm-up"},
                    "main_set": [{"intervals": 5, "duration_min": 3, "intensity": "Zone 5", "recovery_min": 3}],
                    "cooldown": {"duration_min": 10, "description": "Easy spinning"},
                },
                "reasoning": "High aerobic capacity expansion",
            },
            {
                "name": "Easy Aerobic Run",
                "sport_type": "Run",
                "target_duration_min": 40,
                "target_distance_m": 7000.0,
                "target_intensity": 65.0,
                "structure": {
                    "warmup": {"duration_min": 5, "description": "Brisk walk"},
                    "main_set": [{"intervals": 1, "duration_min": 30, "intensity": "Zone 2", "recovery_min": 0}],
                    "cooldown": {"duration_min": 5, "description": "Cool down walk"},
                },
                "reasoning": "Aerobic conditioning without neuromuscular fatigue",
            },
            {
                "name": "Long Weekend Ride",
                "sport_type": "Ride",
                "target_duration_min": 90,
                "target_distance_m": 40000.0,
                "target_intensity": 70.0,
                "structure": {
                    "warmup": {"duration_min": 10, "description": "Gradual spin up"},
                    "main_set": [{"intervals": 1, "duration_min": 70, "intensity": "Zone 2 endurance", "recovery_min": 0}],
                    "cooldown": {"duration_min": 10, "description": "Gentle spin down"},
                },
                "reasoning": "Long duration mitochondrial and endurance stimulus",
            },
            {
                "name": "Rest & Regeneration",
                "sport_type": "Other",
                "target_duration_min": 20,
                "target_distance_m": 0.0,
                "target_intensity": 35.0,
                "structure": {
                    "warmup": {"duration_min": 5, "description": "Breathwork"},
                    "main_set": [{"intervals": 1, "duration_min": 15, "intensity": "Yoga / foam rolling", "recovery_min": 0}],
                    "cooldown": {"duration_min": 0, "description": "Rest"},
                },
                "reasoning": "Complete physiological adaptation and rest",
            },
        ]

        workouts = []
        for day in range(duration):
            template = templates[day % len(templates)]
            week_idx = day // 7
            is_deload = (week_idx == 3)  # Week 4 deload in 28-day blocks
            multiplier = 0.7 if is_deload else (1.0 + (week_idx * 0.05))
            
            dur = max(20, int(template["target_duration_min"] * multiplier))
            dist = round(template["target_distance_m"] * multiplier, 1) if template["target_distance_m"] else 0.0

            workouts.append({
                "day_offset": day,
                "name": f"{template['name']}" if duration <= 7 else f"W{week_idx + 1} {template['name']}",
                "sport_type": template["sport_type"],
                "target_duration_min": dur,
                "target_distance_m": dist,
                "target_intensity": template["target_intensity"],
                "plan_metadata": {
                    "structure": template["structure"],
                    "target_duration_min": dur,
                    "target_intensity": template["target_intensity"],
                    "reasoning": template["reasoning"],
                    "week_number": week_idx + 1,
                    "is_deload": is_deload,
                },
            })

        period_desc = f"{duration}-day progressive block" if duration > 7 else "7-day microcycle"
        return {
            "reasoning": f"Periodized training strategy with progressive overload and recovery for a {period_desc}.",
            "workouts": workouts,
        }



