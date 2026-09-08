import os
import json
from typing import Dict, Any, List, Optional
import httpx


class AIClient:
    """
    Generic AI client configured via AI_API_URL, AI_API_KEY, and AI_MODEL.
    Compatible with standard LLM endpoints (OpenAI-compatible, OpenRouter, Ollama, vLLM, Anthropic, etc.).
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = (
            api_key
            or os.getenv("AI_API_KEY")
            or os.getenv("AI_KEY")
            or os.getenv("ANTHROPIC_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or ""
        )

        self.api_url = (
            api_url
            or os.getenv("AI_API_URL")
            or os.getenv("AI_URL")
            or os.getenv("AI_BASE_URL")
            or ""
        )

        self.model = (
            model
            or os.getenv("AI_MODEL")
            or "default"
        )

    async def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        Calls configured AI API URL and parses the structured JSON response.
        If no API URL or key is provided, returns fallback simulated AI planning.
        """
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
                payload = {
                    "model": self.model if self.model != "default" else "claude-3-5-sonnet-20241022",
                    "max_tokens": 4096,
                    "system": system_prompt + "\nYou must respond with valid raw JSON only, no markdown wrapping.",
                    "messages": [{"role": "user", "content": user_prompt}],
                }
                response = await client.post(target_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                content = data["content"][0]["text"].strip()
            else:
                # Standard OpenAI-compatible format (Ollama, vLLM, OpenRouter, Mistral, Groq, OpenAI, etc.)
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                # Auto-append /chat/completions if given a base URL ending with /v1
                endpoint = target_url
                if endpoint.endswith("/v1") or endpoint.endswith("/v1/"):
                    endpoint = f"{endpoint.rstrip('/')}/chat/completions"

                payload = {
                    "model": self.model if self.model != "default" else "gpt-4o",
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompt + "\nYou must respond with valid raw JSON only, no markdown formatting.",
                        },
                        {"role": "user", "content": user_prompt},
                    ],
                }
                response = await client.post(endpoint, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()

            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            return json.loads(content.strip())

            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            return json.loads(content.strip())

    def _fallback_response(self, user_prompt: str) -> Dict[str, Any]:
        """Deterministic simulation for tests and environments without live AI credentials."""
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


# Alias for backwards compatibility
ClaudeClient = AIClient
