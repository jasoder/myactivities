# MyActivities Full-stack Application

## Architecture and Platforms

- **Unified codebase** using React Native and React Native Web *(planned Phase 2)*
- Single responsive layout targeting mobile and web browsers with identical UI *(future)*
- Asynchronous FastAPI backend
- PostgreSQL database
- Dockerized environment for consistent development/local runs

## Authentication and Onboarding

- **Email & Password Authentication**: Standard JWT Bearer token authentication with argon2 password hashing.
  - `POST /auth/register` creates account and returns JWT token.
  - `POST /auth/login` validates credentials and returns JWT token.
- **Strava OAuth integration**: Optional integration for syncing training history and receiving real-time webhooks.
- Authenticated user endpoints under `/user` provide self-service profile and preference management.
- Google and Apple OAuth planned for Phase 2.

## Landing Page and Calendar

- Focuses on the current training window (day, week, or month views).
- Calendar populates from `GET /myactivities/user/activities?start_date=...&end_date=...` for the authenticated athlete.
- Activities contain `status` (`planned`, `completed`, `missed`, `modified`) and timestamp fields (`planned_date`, `actual_date`).
- Interactive workout management: Create manual workouts (`POST /activities`), drag-and-drop reschedule (`PUT /activities/{id}`), view details (`GET /activities/detail/{id}`), or delete (`DELETE /activities/{id}`).

## AI Features and Adaptive Scheduling

- **Adaptive scheduling**: Analyzes historical activities and calculates training load (CTL, ATL, TSB).
- Supports flexible planning durations from 1 to 60 days (e.g. 7-day microcycle, 28-day 4-week block with deload week).
- Generates structured workout previews via `POST /ai/generate-plan` (backed by LLM or deterministic fallback).
- User inspects and confirms via `POST /ai/confirm-plan`, writing activities directly to the database.
- Weekly recap and coach commentary via `GET /ai/weekly-recap`.
- Supported LLM providers: Anthropic messages API, OpenAI-compatible chat completions, or intelligent fallback templates.

## Workouts

- Users can create workouts via a structured form interface (Title, warmup, sets, cooldown)
- Users can save workouts as templates to reuse on other days
- Users can edit or delete workouts directly on the calendar

## Weekly Recap / Morning Report

- Displayed as an interactive card popup when the user opens the app at the start of a new week
- Shows last week's completed workouts vs. planned workouts and their impact on training load
- Past recaps are archived and accessible in a history section

## Activity Status Flow

All activities are stored in a single `activities` table with a `status` field:

| Status | Meaning |
|--------|---------|
| `planned` | User intends to do this activity (has a `planned_date`) |
| `completed` | Activity was done (has an `actual_date`) |
| `missed` | Planned activity that was skipped |
| `modified` | Planned activity that was changed |

**Workflow:**
1. **Planning** → Insert `Activity(status=planned, planned_date=set)`
2. **Strava Sync** → Match a planned Activity by date/sport and update to `status=completed`, set `actual_date`, link `strava_activity_id`
3. **Unplanned Activity** → Insert new `Activity(status=completed, source=strava)` with no matching plan
4. **Missed** → Planned Activity where `planned_date` passed without Strava match

## Data Model

### Core Activity Table (`activities`)

Shared fields for all activities regardless of status:

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `athlete_id` | UUID (FK) | References `athletes.id` |
| `status` | Enum | planned, completed, missed, modified |
| `source` | Enum | strava, manual |
| `sport_type` | String | Ride, Run, Swim, Other |
| `planned_date` | DateTime | When user intended to do it |
| `actual_date` | DateTime | When activity actually happened |
| `name` | String | Activity name |
| `description` | Text | Optional description |
| `week_plan_id` | UUID (FK) | Links to `week_plans` |
| `matched_strava_activity_id` | String | Links planned → completed via Strava |
| `reconciliation_note` | Text | Manual reconciliation notes |
| `created_at` | DateTime | Record creation |
| `updated_at` | DateTime | Last update |
| `plan_metadata` | JSONB | AI-generated plan details (structure, reasoning) |

### ActivityMetric Table (`activity_metrics`)

Optional 1:1 table for completed activity metrics (FK to `activities`):

| Column | Type | Description |
|--------|------|-------------|
| `activity_id` | UUID (FK) | Primary key, references `activities.id` |
| `distance_m` | Float | Distance in meters |
| `duration_min` | Integer | Duration in minutes |
| `elevation_gain_m` | Float | Elevation gain |
| `average_speed_mps` | Float | Average speed |
| `average_hr_bpm` | Float | Average heart rate |
| `max_hr_bpm` | Float | Max heart rate |
| `average_power_w` | Float | Average power |
| `calories_kcal` | Float | Calories burned |
| `device_name` | String | Connected device |

**Only populated when `status=completed`.** The `ActivityMetric` table stays NULL for planned activities.

### Week Plans Table (`week_plans`)

Groups the 7 planned rows generated together by Claude's planning service.

### Training Preferences Table (`training_preferences`)

One row per athlete storing training preferences used by the AI planning service.

## API Endpoints (Backend)
 
Mounted at `/api/v1` with prefix `/myactivities`:
- `/myactivities/auth` - User registration and authentication (`/register`, `/login`)
- `/myactivities/user` - Authenticated athlete profile, preferences, calendar activities, and Strava disconnect
- `/myactivities/activities` - Activity CRUD operations (`/`, `/detail/{id}`, `/{id}`)
- `/myactivities/strava` - Strava OAuth flow, manual sync (`/sync`), and webhook ingestion (`/webhook`)
- `/myactivities/ai` - AI planning (`/generate-plan`, `/confirm-plan`), training load analytics (`/training-load`), and weekly recaps (`/weekly-recap`)

**No legacy routes**: `/completedActivities`, `/plannedActivities`, and unauthenticated `/athletes` endpoints have been removed.

## Database Migration Strategy

**Unified Activity Model**: Legacy tables (`completed_activities`, `planned_activities`) and their associated services, schemas, and API routes have been removed. All activity data moves through the unified `activities` table with composite DB indexes:
- `idx_activities_athlete_planned (athlete_id, planned_date)`
- `idx_activities_athlete_actual (athlete_id, actual_date)`
- `idx_activities_athlete_status (athlete_id, status)`
- `idx_week_plans_athlete_start (athlete_id, week_start_date)`

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Database connection string |
| `SECRET_KEY` | Yes | Secret key for JWT signing |
| `STRAVA_CLIENT_ID` | Optional | Strava OAuth client ID |
| `STRAVA_CLIENT_SECRET` | Optional | Strava OAuth client secret |
| `STRAVA_VERIFY_TOKEN` | Optional | Verification token for Strava webhooks |
| `AI_API_URL` | Optional | URL for AI service (OpenAI-compatible or Anthropic endpoint) |
| `AI_API_KEY` | Optional | API key for AI provider |
| `AI_MODEL` | Optional | Model identifier for AI completions |
| `ALLOWED_ORIGINS` | Optional | Allowed CORS origins for frontend |

## Running Tests

```bash
pytest
```

## Project Structure

```
src/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── core/                # Core configuration & security (JWT, argon2)
│   ├── api/
│   │   ├── api_router.py    # Main router
│   │   └── routers/         # API endpoints (auth, user, activities, strava, ai)
│   ├── db/
│   │   ├── base.py          # SQLAlchemy base
│   │   ├── session.py       # DB session manager
│   │   └── manage.py        # Database initialization
│   ├── models/              # SQLAlchemy models (Activity, ActivityMetric, WeekPlan, TrainingPreference, Athlete)
│   ├── schemas/             # Pydantic schemas (activities, athlete, auth, errors)
│   ├── services/            # Business logic (activities_service, athlete_service, auth_service, strava_sync_service)
│   ├── integrations/        # External integrations (Strava client)
│   └── ai/                  # AI assistant services (planner_service, load_analysis_service, client)
├── tests/                   # Pytest test suite
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── requirements_spec.md
```

## AI Integration Details (Implemented)

The AI adaptive scheduling feature includes:
1. `src/app/ai/client.py`: Multi-provider AI client supporting Anthropic, OpenAI-compatible APIs, and built-in physiological fallback generators.
2. `src/app/ai/load_analysis_service.py`: Training load analysis service calculating Chronic Training Load (CTL), Acute Training Load (ATL), and Training Stress Balance (TSB).
3. `src/app/ai/planner_service.py`: Arbitrary duration plan generator (1 to 60 days) with periodization and deload cycles.
4. Confirmation flow: AI outputs preview (`POST /ai/generate-plan`) → user inspects/edits → user confirms (`POST /ai/confirm-plan`) → writes `Activity` records to database.
5. Weekly recap generation (`GET /ai/weekly-recap`) analyzing planned vs actual workouts and volume adherence.
