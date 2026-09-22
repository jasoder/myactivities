# MyActivities Domain Model

## Glossary

### Activity
A single workout entry in the unified `activities` table. An Activity can be in one of several states (`status`): `planned`, `completed`, `missed`, or `modified`.

**Distinction**: An `Activity` represents the full lifecycle of a workout — from user intention (planned) to reality (completed). This replaces the previous split between `PlannedActivity` and `CompletedActivity` models.

### Planned Activity vs Completed Activity
These are not separate database entities. They are the same `Activity` at different stages:
- **Planned**: Has `planned_date`, `status=planned`, no `actual_date`
- **Completed**: Has `actual_date`, `status=completed`
- **Missed**: `status=missed` after `planned_date` passes without a Strava match

### ActivityMetric
Optional 1:1 table linked to `Activity` via FK. Only populated when `status=completed`. Contains performance metrics (distance, duration, HR, power, calories, etc.).

### Strava Sync
The process of matching Strava activities with planned activities by sport type and date. When a match is found, the planned Activity is updated to `status=completed` and linked via `matched_strava_activity_id`. When no match is found, a new `Activity(status=completed, source=strava)` is created.

### Adaptive Scheduling
AI-powered feature that analyzes completed workouts and adjusts future training plans. Generates workouts for arbitrary horizons (1 to 60 days, e.g. 7-day microcycles or 28-day 4-week blocks with deload) based on historical performance data and training load (CTL, ATL, TSB).

### WeekPlan
Database entity grouping planned activities generated together by the AI planning service. Scopes planning blocks and reconciliations by `(athlete_id, week_start_date)`.

### TrainingPreference
One row per athlete storing sport targets, rest days, and weekly limits. Used by the AI planning service to understand user constraints.

### Reconciliation
The process of matching completed workouts (from Strava) with planned calendar workouts. Uses sport type, duration, and date to auto-match. A manual option exists to link or unlink workouts if the automatic match is incorrect.

### Unified Migration
Migration where legacy tables (`completed_activities`, `planned_activities`), redundant routes (`/athletes`, legacy AI endpoints), and unauthenticated endpoints were replaced with a clean, authenticated architecture.

## Decisions

| Decision | Rationale |
|----------|-----------|
| Unified Activity table | Single table for all activities simplifies calendar queries and avoids joins |
| Split core + metrics | Metrics only apply to completed activities; keeping them separate avoids NULL columns for planned activities |
| Status-based model | `status` field (planned/completed/missed/modified) captures activity lifecycle; `planned_date` and `actual_date` capture intent vs reality |
| Composite DB Indexes | `(athlete_id, planned_date)`, `(athlete_id, actual_date)`, `(athlete_id, status)`, and `(athlete_id, week_start_date)` ensure fast range queries at scale |
| Arbitrary Plan Horizons | AI planner supports 1–60 days, enabling full month (4-week periodized) plan generation with deload weeks |
| Bearer JWT Auth | Secure email/password authentication with argon2 hashing and current user inference eliminates unauthenticated IDOR risks |
| Multi-provider AI Client | Supports OpenAI-compatible endpoints, Anthropic messages format, and physiological fallback generators |

## Edge Cases & Scenarios

### Scenario 1: User Plans Workout, Completes Different Workout
- User creates `Activity(status=planned, planned_date=Tuesday, sport_type=Run)`
- Strava sync finds a Ride on Tuesday (different sport)
- **Rule**: Auto-match requires sport_type match within ±1 day. Different sport = no match
- Result: New `Activity(status=completed, source=strava, sport_type=Ride, actual_date=Tuesday)` created; original Run stays planned

### Scenario 2: User Skips Planned Workout
- `Activity(status=planned, planned_date=Monday)` exists
- Monday passes, no Strava activity matches
- **Auto-missed**: Daily job marks `status=missed` for activities where `planned_date < now` AND no Strava match
- User can also manually mark `status=missed` anytime

### Scenario 3: User Does Unplanned Activity
- No planned activity for Wednesday
- Strava sync finds Run on Wednesday
- **Result**: New `Activity(status=completed, source=strava, actual_date=Wednesday)` — no link to any plan

### Scenario 4: User Modifies Planned Workout After Completion
- Planned: `Activity(status=planned, planned_date=Friday)`
- Strava matches → `status=completed`, `actual_date=Friday`
- User edits the activity (changes name, adds notes)
- **Rule**: `status=modified` (preserves link to original plan, indicates user override)

### Scenario 5: Multiple Strava Activities Match One Plan
- Planned: `Activity(status=planned, sport_type=Run, planned_date=Saturday)`
- Strava has two Runs on Saturday (morning + evening)
- **Rule**: Match the closest by duration to plan's `duration_min`. Other Strava activity becomes new `status=completed` (unplanned)

## plan_metadata Field Semantics

JSONB field on `Activity` populated by AI planning service:

```json
{
  "structure": {
    "warmup": {"duration_min": 15, "description": "Easy jog"},
    "main_set": [
      {"intervals": 4, "duration_min": 4, "intensity": "threshold", "recovery_min": 3}
    ],
    "cooldown": {"duration_min": 10, "description": "Easy jog"}
  },
  "target_duration_min": 60,
  "target_intensity": "tempo",
  "reasoning": "Building lactate tolerance for upcoming race",
  "progression_week": 3
}
```

Only set when `source=manual` or `source=ai_generated`. Not populated from Strava.

## Reconciliation Scenarios

| Scenario | Auto-match? | Manual action needed? |
|----------|-------------|----------------------|
| Strava activity matches planned by sport + date ±1 day | Yes | No |
| Strava activity matches but duration differs >50% | Partial | User confirms/rejects |
| Two Strava activities match one planned | Partial | User picks correct one |
| Strava activity has no planned match | No | User can link to nearby plan |
| Planned activity has no Strava match after date passes | No | Auto-missed or user marks completed |

## Activity Status Flow Diagram

```
┌─────────────┐
│   PLANNED   │ ← User creates / AI generates
│ (planned_date)     │
└──────┬──────┘
       │ Strava sync finds match
       ▼
┌─────────────┐     ┌───────────┐
│  COMPLETED  │────▶│  MODIFIED │
│ (actual_date)     │ (user edit)│
└──────┬──────┘     └───────────┘
       │
       │ Planned date passes, no match
       ▼
┌─────────────┐
│    MISSED   │
└─────────────┘
```

## Cross-Reference with Code

| Domain Term | Code Location |
|-------------|---------------|
| Activity | `src/app/models/activities.py` (`Activity` model) |
| ActivityMetric | `src/app/models/activities.py` (`ActivityMetric` model) |
| ActivityStatus / Source | `src/app/enums.py` (`ActivityStatus`, `ActivitySource`) |
| WeekPlan | `src/app/models/activities.py` (`WeekPlan` model) |
| TrainingPreference | `src/app/models/activities.py` (`TrainingPreference` model) |
| Athlete / User | `src/app/models/athlete.py` (`Athlete` model) |
| Authentication | `src/app/core/security.py`, `src/app/services/auth_service.py` |
| Strava Sync & Webhooks | `src/app/services/strava_sync_service.py`, `src/app/integrations/strava/client.py` |
| Adaptive Scheduling & Plans | `src/app/ai/planner_service.py`, `src/app/ai/client.py` |
| Training Load Analytics | `src/app/ai/load_analysis_service.py` |
