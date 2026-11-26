# MyActivities Domain Model

## Core Concepts

- **Activity** (`src/app/models/activities.py`): Unified table for all workouts across their lifecycle (`status`: `planned`, `completed`, `missed`, `modified`).
  - `planned`: has `planned_date`
  - `completed`: has `actual_date` (preserves original day when marked complete)
  - `missed`: `planned_date` passed without a match
  - `modified`: completed workout edited by the user
- **ActivityMetric** (`src/app/models/activities.py`): Optional 1:1 telemetry for completed activities (distance, duration, HR, power, calories).
- **WeekPlan** (`src/app/models/activities.py`): Groups AI-generated planned workouts created together.
- **TrainingPreference** (`src/app/models/activities.py`): Per-athlete weekly volume, max training days, rest days, and split notes.
- **Strava Sync** (`src/app/services/strava_sync_service.py`): Matches Strava workouts to `planned` activities by sport and date (±1 day), or inserts unplanned `completed` activities.
- **AI Coach** (`src/app/ai/planner_service.py`, `src/app/ai/client.py`): Analyzes CTL/ATL/TSB load and existing planned workouts to generate, add, swap, or remove workouts without unintended duplicates.

## Key Decisions

| Decision | Why |
|----------|-----|
| Unified `activities` table | Single range query for calendar views; avoids planned/completed joins |
| Separate `activity_metrics` table | Avoids NULL telemetry columns on planned workouts |
| Composite DB indexes | Fast calendar and load queries on `(athlete_id, planned_date/actual_date/status)` |
| JWT Bearer auth | Infers `athlete_id` from token to prevent IDOR |
| Multi-provider AI + fallback | Works with OpenAI-compatible APIs, Anthropic, or offline fallback templates |
