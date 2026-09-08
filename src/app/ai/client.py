import os
import json
from typing import Dict, Any, List, Optional
import httpx


class AIClient:
    """
    Flexible AI client supporting Anthropic, OpenAI, OpenRouter, Ollama,
    and other OpenAI-compatible endpoints configured via environment variables.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        # 1. Resolve API Key
        self.api_key = (
            api_key
            or os.getenv("AI_API_KEY")
            or os.getenv("ANTHROPIC_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or ""
        )

        # 2. Resolve Provider ('anthropic' or 'openai' / 'openai_compatible' / 'ollama' / 'openrouter')
        raw_provider = provider or os.getenv("AI_PROVIDER")
        if not raw_provider:
            if os.getenv("OPENAI_API_KEY") or (os.getenv("AI_API_URL", "").find("openai") != -1) or (os.getenv("AI_API_URL", "").find("11434") != -1):
                raw_provider = "openai"
            else:
                raw_provider = "anthropic"
        self.provider = raw_provider.lower().strip()

        # 3. Resolve API URL
        env_url = (
            api_url
            or os.getenv("AI_API_URL")
            or os.getenv("AI_BASE_URL")
            or os.getenv("ANTHROPIC_API_URL")
        )
        if env_url:
            self.api_url = env_url
            # If user provided a base URL ending in /v1 for OpenAI/Ollama, ensure endpoint is complete
            if self.provider in ["openai", "openai_compatible", "ollama", "openrouter"]:
                if not self.api_url.endswith("/chat/completions"):
                    self.api_url = f"{self.api_url.rstrip('/')}/chat/completions"
        else:
            if self.provider in ["openai", "openai_compatible"]:
                self.api_url = "https://api.openai.com/v1/chat/completions"
            elif self.provider == "openrouter":
                self.api_url = "https://openrouter.ai/api/v1/chat/completions"
            elif self.provider == "ollama":
                self.api_url = "http://localhost:11434/v1/chat/completions"
            else:
                self.api_url = "https://api.anthropic.com/v1/messages"

        # 4. Resolve Model
        default_model = "gpt-4o" if self.provider in ["openai", "openai_compatible"] else "claude-3-5-sonnet-20241022"
        self.model = (
            model
            or os.getenv("AI_MODEL")
            or os.getenv("ANTHROPIC_MODEL")
            or os.getenv("OPENAI_MODEL")
            or default_model
        )

    async def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        Calls configured AI API (Anthropic or OpenAI-compatible) and parses the structured JSON response.
        If no API key or local endpoint is provided, returns fallback simulated AI planning.
        """
        # Allow keyless calls for local Ollama endpoints; otherwise require API key
        is_local = "localhost" in self.api_url or "127.0.0.1" in self.api_url
        if not self.api_key and not is_local:
            return self._fallback_response(user_prompt)

        async with httpx.AsyncClient(timeout=45.0) as client:
            if self.provider in ["openai", "openai_compatible", "ollama", "openrouter"]:
                headers = {
                    "Content-Type": "application/json",
                }
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                payload = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompt + "\nYou must respond with valid raw JSON only, no markdown formatting.",
                        },
                        {"role": "user", "content": user_prompt},
                    ],
                }
                response = await client.post(self.api_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()
            else:
                # Default to Anthropic format
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
                response = await client.post(self.api_url, headers=headers, json=payload)
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
