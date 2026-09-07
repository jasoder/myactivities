# MyActivities Full-stack Application

## Architecture and Platforms

- **Unified codebase** using React Native and React Native Web *(planned Phase 2)*
- Single responsive layout targeting mobile and web browsers with identical UI *(future)*
- Asynchronous FastAPI backend
- PostgreSQL database
- Dockerized environment for consistent development/local runs

## Authentication and Onboarding

- **OAuth-only login** with no username/password registration
- Initial Strava OAuth integration (MVP)
- Onboarding imports initial training history from Strava and sets user preferences
- Each athlete has unique OAuth credentials stored securely
- Google and Apple OAuth planned for Phase 2

## Landing Page and Calendar

- Focuses on the current week (Monday to Sunday)
- Current week strip is shown at the top of the landing page
- Bottom navigation bar houses main tabs
- Users can swipe horizontally to navigate back to history or forward to planned weeks
- Weekly calendar view with day-by-day workout grid
- Calendar populates from the unified `/activities` endpoint, filtering by `status` and `planned_date`

## AI Features and Adaptive Scheduling

- **Adaptive scheduling**: Analyzes completed workouts and adjusts future plans based on performance data
- Automatically calculates historical training load from synced Strava data
- Allows manual user overrides for training experience, weekly hour targets, and goals
- Adjusts future training schedules dynamically based on performance data
- Generates next week's workouts during the weekly recap or when triggered by the user
- Powered by Claude API (Anthropic) for workout planning and reasoning
- AI outputs changes as a preview; user confirms before writing to database

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
| `source` | Enum | strava, intervals, manual |
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
| `icu_training_load` | Float | Intervals.icu training load |
| `device_name` | String | Connected device |

**Only populated when `status=completed`.** The `ActivityMetric` table stays NULL for planned activities.

### Week Plans Table (`week_plans`)

Groups the 7 planned rows generated together by Claude's planning service.

### Training Preferences Table (`training_preferences`)

One row per athlete storing training preferences used by the AI planning service.

## API Endpoints (Backend)

- `/myactivities/athletes` - Athlete management with OAuth flow
- `/myactivities/activities` - Unified activities view (single endpoint for all activity types)
  - `GET /{athlete_id}?start_date=&end_date=` - Returns calendar events combining planned + completed activities
- `/myactivities/strava` - Strava integration webhooks and OAuth callback

**No legacy routes**: `/completedActivities` and `/plannedActivities` have been removed. All activity data flows through `/activities`.

## Database Migration Strategy

**Big bang migration**: Legacy tables (`completed_activities`, `planned_activities`) and their associated services, schemas, and API routes are removed. All activity data moves to the unified `activities` table.

- Legacy models deleted: `CompletedActivity`, `PlannedActivity`
- Legacy services deleted: `completed_activity_service`, `planned_activity_service`
- Legacy routes deleted: `/completedActivities`, `/plannedActivities`
- All services updated to use unified `Activity` model
- Athlete model relationships updated to remove legacy references

## Intervals.icu Integration

Removed from MVP. The Intervals.icu integration service was broken and is not required for the core MVP. Intervals.icu support can be re-added as a Phase 2 feature.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Database connection string |
| `STRAVA_CLIENT_ID` | Yes (MVP) | Strava OAuth client ID |
| `STRAVA_CLIENT_SECRET` | Yes (MVP) | Strava OAuth client secret |
| `ANTHROPIC_API_KEY` | Yes | Claude API key for AI features |
| Additional OAuth keys | Optional | Google/Apple client IDs for Phase 2 |

## Running Tests

```bash
pytest
# Or specific test files
pytest tests/unit/test_*.py
```

## Docker Compose

```yaml
services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: myactivities
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: myactivities
    volumes:
      - pg_data:/var/lib/postgresql/data
  api:
    build: ./src
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:myactivities@db:5432/myactivities
      STRAVA_CLIENT_ID: ${STRAVA_CLIENT_ID}
      STRAVA_CLIENT_SECRET: ${STRAVA_CLIENT_SECRET}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
    ports:
      - "8000:8000"
volumes:
  pg_data:
```

## Project Structure

```
src/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── api/
│   │   ├── api_router.py    # Main router
│   │   └── routers/         # API endpoints (athletes, activities, strava)
│   ├── db/
│   │   ├── base.py          # SQLAlchemy base
│   │   └── manage.py        # Database initialization
│   ├── models/              # SQLAlchemy models (Activity, ActivityMetric, WeekPlan, TrainingPreference, Athlete)
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic (activities_service, athlete_service, strava_sync_service)
│   ├── integrations/        # External integrations (Strava)
│   └── ai/                  # AI assistant services (adaptive scheduling)
├── tests/
│   ├── unit/
│   └── integration/
├── scripts/
│   ├── seed_db.py
│   └── init_db.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── requirements_spec.md
```

## TODO: Frontend Implementation

The React Native + React Native Web frontend is planned as a separate but coordinated effort. The backend API is the foundation; frontend work follows the architecture defined in this spec. *(Phase 2)*

## TODO: AI Integration Details

The AI adaptive scheduling feature requires:
1. `src/app/ai/` directory with Claude API client
2. Training load analysis service that reads completed activities and generates adjustments
3. Workout planning service that creates `Activity` records with `plan_metadata`
4. Confirmation flow: AI outputs preview → user confirms → writes to database
5. Weekly recap generation based on completed vs planned activities
