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

        try:
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
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(
                "AI provider failed (%s). Using adaptive fallback engine.", exc
            )
            return self._fallback_response(user_prompt)

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
        from datetime import datetime, timedelta

        duration = 7
        match = re.search(r"(\d+)-day", user_prompt)
        if match:
            duration = int(match.group(1))
        else:
            match = re.search(r"Duration:\s*(\d+)", user_prompt)
            if match:
                duration = int(match.group(1))

        # 1. Parse Preferred Sports
        preferred_sports = ["Run", "Ride"]
        sports_match = re.search(r"Preferred Sports:\s*\[(.*?)\]", user_prompt)
        if sports_match:
            parsed_sports = [s.strip(" '\"") for s in sports_match.group(1).split(",") if s.strip(" '\"")]
            if parsed_sports:
                preferred_sports = parsed_sports

        # 2. Parse Designated Rest Days
        rest_days = []
        rest_match = re.search(r"Designated Rest Days:\s*\[(.*?)\]", user_prompt)
        if rest_match:
            rest_days = [d.strip(" '\"") for d in rest_match.group(1).split(",") if d.strip(" '\"")]

        # 3. Parse Weekly Training Hours
        weekly_hours = 6.0
        hours_match = re.search(r"Weekly Training Hours Target:\s*([0-9.]+)", user_prompt)
        if hours_match:
            try:
                weekly_hours = float(hours_match.group(1))
            except ValueError:
                pass

        # 4. Parse Max Days Per Week
        max_days = 6
        max_days_match = re.search(r"Max Days Per Week:\s*(\d+)", user_prompt)
        if max_days_match:
            try:
                max_days = int(max_days_match.group(1))
            except ValueError:
                pass

        # 5. Parse Split Notes & Athlete Request
        split_notes = ""
        notes_match = re.search(r"Training Focus & Split Notes:\s*([^\n]+)", user_prompt)
        if notes_match and notes_match.group(1).strip() not in ("None specified", "None"):
            split_notes = notes_match.group(1).strip()

        user_request = ""
        req_match = re.search(r"Athlete Request / Chat Prompt:\s*([^\n]+)", user_prompt)
        if req_match and req_match.group(1).strip() not in ("None specified", "None"):
            user_request = req_match.group(1).strip()

        # 6. Parse Start Date
        start_date = None
        date_match = re.search(r"Plan start date:\s*([0-9T:-]+)", user_prompt)
        if date_match:
            try:
                clean_date_str = date_match.group(1).replace("Z", "+00:00")
                start_date = datetime.fromisoformat(clean_date_str)
            except Exception:
                pass

        # Sport-specific session library
        sport_templates: Dict[str, List[Dict[str, Any]]] = {
            "Run": [
                {
                    "name": "Tempo Intervals Run",
                    "sport_type": "Run",
                    "base_duration": 45,
                    "target_distance_m": 8000.0,
                    "target_intensity": 85.0,
                    "structure": {
                        "warmup": {"duration_min": 10, "description": "Easy jog"},
                        "main_set": [{"intervals": 3, "duration_min": 8, "intensity": "Zone 4 Tempo", "recovery_min": 2}],
                        "cooldown": {"duration_min": 5, "description": "Walking cool-down"},
                    },
                    "reasoning": "Lactate threshold stimulus and anaerobic buffer expansion",
                },
                {
                    "name": "Aerobic Base Run",
                    "sport_type": "Run",
                    "base_duration": 50,
                    "target_distance_m": 9000.0,
                    "target_intensity": 68.0,
                    "structure": {
                        "warmup": {"duration_min": 5, "description": "Brisk walk to easy jog"},
                        "main_set": [{"intervals": 1, "duration_min": 40, "intensity": "Zone 2 Steady", "recovery_min": 0}],
                        "cooldown": {"duration_min": 5, "description": "Gentle jog"},
                    },
                    "reasoning": "Mitochondrial development and fat oxidation capacity",
                },
                {
                    "name": "VO2 Max Speed Run",
                    "sport_type": "Run",
                    "base_duration": 40,
                    "target_distance_m": 7000.0,
                    "target_intensity": 90.0,
                    "structure": {
                        "warmup": {"duration_min": 10, "description": "Dynamic drills & progressive strides"},
                        "main_set": [{"intervals": 5, "duration_min": 3, "intensity": "Zone 5 Max Aerobic", "recovery_min": 2.5}],
                        "cooldown": {"duration_min": 5, "description": "Walking cool-down"},
                    },
                    "reasoning": "Peak aerobic capacity expansion and neuromuscular velocity",
                },
                {
                    "name": "Long Endurance Run",
                    "sport_type": "Run",
                    "base_duration": 80,
                    "target_distance_m": 15000.0,
                    "target_intensity": 70.0,
                    "structure": {
                        "warmup": {"duration_min": 10, "description": "Easy conversation pace"},
                        "main_set": [{"intervals": 1, "duration_min": 60, "intensity": "Zone 2 Long Aerobic", "recovery_min": 0}],
                        "cooldown": {"duration_min": 10, "description": "Walking cool-down"},
                    },
                    "reasoning": "Musculoskeletal durability and glycogen depletion resilience",
                },
                {
                    "name": "Easy Recovery Jog",
                    "sport_type": "Run",
                    "base_duration": 30,
                    "target_distance_m": 4500.0,
                    "target_intensity": 60.0,
                    "structure": {
                        "warmup": {"duration_min": 5, "description": "Gentle walk"},
                        "main_set": [{"intervals": 1, "duration_min": 20, "intensity": "Zone 1 Active Recovery", "recovery_min": 0}],
                        "cooldown": {"duration_min": 5, "description": "Light calf & hamstring stretching"},
                    },
                    "reasoning": "Promote blood flow and expedite clearance without structural fatigue",
                },
            ],
            "Ride": [
                {
                    "name": "Sweet Spot Intervals Ride",
                    "sport_type": "Ride",
                    "base_duration": 60,
                    "target_distance_m": 28000.0,
                    "target_intensity": 86.0,
                    "structure": {
                        "warmup": {"duration_min": 10, "description": "Progressive cadence spin"},
                        "main_set": [{"intervals": 3, "duration_min": 10, "intensity": "Sweet Spot 88-93% FTP", "recovery_min": 3}],
                        "cooldown": {"duration_min": 10, "description": "Easy spinning"},
                    },
                    "reasoning": "High-efficiency aerobic engine and threshold power progression",
                },
                {
                    "name": "Base Endurance Ride",
                    "sport_type": "Ride",
                    "base_duration": 65,
                    "target_distance_m": 30000.0,
                    "target_intensity": 68.0,
                    "structure": {
                        "warmup": {"duration_min": 10, "description": "Easy spin"},
                        "main_set": [{"intervals": 1, "duration_min": 45, "intensity": "Zone 2 Aerobic", "recovery_min": 0}],
                        "cooldown": {"duration_min": 10, "description": "Cool down spin"},
                    },
                    "reasoning": "Capillary density and aerobic efficiency",
                },
                {
                    "name": "VO2 Max Hill Repeats Ride",
                    "sport_type": "Ride",
                    "base_duration": 50,
                    "target_distance_m": 22000.0,
                    "target_intensity": 92.0,
                    "structure": {
                        "warmup": {"duration_min": 15, "description": "Gradual ramp-up with high cadence openers"},
                        "main_set": [{"intervals": 5, "duration_min": 3, "intensity": "Zone 5 VO2 Max 110-115% FTP", "recovery_min": 3}],
                        "cooldown": {"duration_min": 10, "description": "Easy spin down"},
                    },
                    "reasoning": "Cardiac stroke volume expansion and high-power repeatability",
                },
                {
                    "name": "Long Weekend Ride",
                    "sport_type": "Ride",
                    "base_duration": 95,
                    "target_distance_m": 45000.0,
                    "target_intensity": 70.0,
                    "structure": {
                        "warmup": {"duration_min": 10, "description": "Gradual spin up"},
                        "main_set": [{"intervals": 1, "duration_min": 75, "intensity": "Zone 2 Endurance", "recovery_min": 0}],
                        "cooldown": {"duration_min": 10, "description": "Gentle spin down"},
                    },
                    "reasoning": "Extended fat oxidation and metabolic endurance",
                },
                {
                    "name": "Recovery Spin",
                    "sport_type": "Ride",
                    "base_duration": 35,
                    "target_distance_m": 15000.0,
                    "target_intensity": 55.0,
                    "structure": {
                        "warmup": {"duration_min": 5, "description": "Light resistance"},
                        "main_set": [{"intervals": 1, "duration_min": 25, "intensity": "Zone 1 Light Spinning", "recovery_min": 0}],
                        "cooldown": {"duration_min": 5, "description": "Gentle spin"},
                    },
                    "reasoning": "Flush lactic metabolites with minimal neuromuscular stress",
                },
            ],
            "Swim": [
                {
                    "name": "Pace & Threshold Intervals Swim",
                    "sport_type": "Swim",
                    "base_duration": 45,
                    "target_distance_m": 2200.0,
                    "target_intensity": 82.0,
                    "structure": {
                        "warmup": {"duration_min": 10, "description": "200m easy choice + 100m kick"},
                        "main_set": [{"intervals": 6, "duration_min": 4, "intensity": "CSS Threshold Pace", "recovery_min": 1}],
                        "cooldown": {"duration_min": 5, "description": "150m easy backstroke / breaststroke"},
                    },
                    "reasoning": "Critical swim speed maintenance and pacing discipline",
                },
                {
                    "name": "Aerobic Distance Swim",
                    "sport_type": "Swim",
                    "base_duration": 50,
                    "target_distance_m": 2500.0,
                    "target_intensity": 70.0,
                    "structure": {
                        "warmup": {"duration_min": 10, "description": "300m easy warm-up"},
                        "main_set": [{"intervals": 1, "duration_min": 35, "intensity": "Steady Zone 2 Freestyle", "recovery_min": 0}],
                        "cooldown": {"duration_min": 5, "description": "100m easy cool-down"},
                    },
                    "reasoning": "Upper body cardiovascular base and stroke consistency",
                },
            ],
            "WeightTraining": [
                {
                    "name": "Full Body Strength & Core",
                    "sport_type": "WeightTraining",
                    "base_duration": 45,
                    "target_distance_m": 0.0,
                    "target_intensity": 75.0,
                    "structure": {
                        "warmup": {"duration_min": 10, "description": "Dynamic mobility and glute activation"},
                        "main_set": [{"intervals": 4, "duration_min": 6, "intensity": "Squats, Deadlifts, Pull-ups", "recovery_min": 2}],
                        "cooldown": {"duration_min": 5, "description": "Full body stretch"},
                    },
                    "reasoning": "Injury prevention, core rigidity, and power transmission",
                },
            ],
            "Other": [
                {
                    "name": "Active Recovery & Mobility",
                    "sport_type": "Other",
                    "base_duration": 30,
                    "target_distance_m": 0.0,
                    "target_intensity": 50.0,
                    "structure": {
                        "warmup": {"duration_min": 5, "description": "Dynamic stretching"},
                        "main_set": [{"intervals": 1, "duration_min": 20, "intensity": "Mobility & core", "recovery_min": 0}],
                        "cooldown": {"duration_min": 5, "description": "Static stretch"},
                    },
                    "reasoning": "Promote recovery and soft tissue health",
                },
            ],
        }

        WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        workouts = []
        for week_idx in range((duration + 6) // 7):
            days_in_this_week = min(7, duration - (week_idx * 7))
            is_deload = (week_idx == 3)  # Week 4 deload in 28-day blocks
            deload_multiplier = 0.7 if is_deload else 1.0

            active_days_count = 0
            for day_in_week in range(days_in_this_week):
                day = (week_idx * 7) + day_in_week

                # Determine weekday name
                if start_date:
                    cur_date = start_date + timedelta(days=day)
                    weekday_name = cur_date.strftime("%A")
                else:
                    weekday_name = WEEKDAY_NAMES[day_in_week % 7]

                # Check if this day is a designated rest day or exceeds max days per week
                is_rest_day = (weekday_name in rest_days) or (active_days_count >= max_days)

                if is_rest_day:
                    workouts.append({
                        "day_offset": day,
                        "name": "Rest & Regeneration" if duration <= 7 else f"W{week_idx + 1} Rest & Regeneration",
                        "sport_type": "Other",
                        "target_duration_min": 0,
                        "target_distance_m": 0.0,
                        "target_intensity": 0.0,
                        "plan_metadata": {
                            "structure": {
                                "warmup": {"duration_min": 0, "description": "Rest"},
                                "main_set": [{"intervals": 1, "duration_min": 0, "intensity": "Complete Rest", "recovery_min": 0}],
                                "cooldown": {"duration_min": 0, "description": "Rest"},
                            },
                            "target_duration_min": 0,
                            "target_intensity": 0.0,
                            "reasoning": f"Scheduled rest on {weekday_name} per athlete preferences.",
                            "week_number": week_idx + 1,
                            "is_deload": is_deload,
                        },
                    })
                else:
                    active_days_count += 1
                    # Select sport from athlete preferred sports
                    sport = preferred_sports[(active_days_count - 1) % len(preferred_sports)]
                    templates_for_sport = sport_templates.get(sport) or sport_templates["Run"]
                    template = templates_for_sport[(active_days_count - 1) % len(templates_for_sport)]

                    # Scale duration according to weekly hours target
                    target_active_days = max(1, min(max_days, 7 - len([d for d in rest_days if d in WEEKDAY_NAMES])))
                    target_minutes_per_session = (weekly_hours * 60) / target_active_days
                    volume_scale = target_minutes_per_session / max(30, template["base_duration"])
                    
                    computed_duration = max(20, int(template["base_duration"] * volume_scale * deload_multiplier))
                    computed_distance = round(template["target_distance_m"] * volume_scale * deload_multiplier, 1) if template.get("target_distance_m") else 0.0

                    # Adjust structure durations
                    warmup_min = max(5, int(computed_duration * 0.15))
                    cooldown_min = max(5, int(computed_duration * 0.12))
                    main_min = computed_duration - warmup_min - cooldown_min

                    workouts.append({
                        "day_offset": day,
                        "name": f"{template['name']}" if duration <= 7 else f"W{week_idx + 1} {template['name']}",
                        "sport_type": template["sport_type"],
                        "target_duration_min": computed_duration,
                        "target_distance_m": computed_distance,
                        "target_intensity": template["target_intensity"],
                        "plan_metadata": {
                            "structure": {
                                "warmup": {"duration_min": warmup_min, "description": template["structure"]["warmup"]["description"]},
                                "main_set": [{"intervals": template["structure"]["main_set"][0]["intervals"], "duration_min": main_min, "intensity": template["structure"]["main_set"][0]["intensity"], "recovery_min": template["structure"]["main_set"][0].get("recovery_min", 2)}],
                                "cooldown": {"duration_min": cooldown_min, "description": template["structure"]["cooldown"]["description"]},
                            },
                            "target_duration_min": computed_duration,
                            "target_intensity": template["target_intensity"],
                            "reasoning": template["reasoning"],
                            "week_number": week_idx + 1,
                            "is_deload": is_deload,
                        },
                    })

        period_desc = f"{duration}-day progressive block" if duration > 7 else "7-day microcycle"
        notes_fragment = f" Focus: {split_notes or user_request}." if (split_notes or user_request) else ""
        rest_fragment = f" Rest days on {', '.join(rest_days)}." if rest_days else ""
        reasoning_str = (
            f"Personalized periodized plan for a {period_desc}. "
            f"Tailored to {', '.join(preferred_sports)}, targeting ~{weekly_hours}h/week across max {max_days} days/week.{rest_fragment}{notes_fragment}"
        )

        return {
            "reasoning": reasoning_str,
            "workouts": workouts,
        }



