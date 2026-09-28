# CLAUDE.md

This file provides guidance when working with code in this repository.

**Common Development Commands:**

- **Backend Setup & Run:**
  - **Install dependencies**: `pip install -r requirements.txt`
  - **Start backend server**: `cd src && uvicorn app.main:app --reload`
  - **Run backend test suite**: `pytest`
  - **Run specific test**: `pytest tests/test_user.py`

- **Frontend Setup & Run:**
  - **Install dependencies**: `cd frontend && npm install`
  - **Start dev server**: `cd frontend && npm run dev` (available at `http://localhost:5173`)
  - **Build & typecheck**: `cd frontend && npm run build`
  - **Generate API types**: `cd frontend && npm run api:generate`

- **Docker & Database:**
  - **Start all containers**: `docker compose up --build -d`
  - **Stop containers**: `docker compose down`
  - **PostgreSQL CLI (psql)**: `docker compose exec db psql -U postgres -d myactivities-test`

**Code Architecture Overview:**

1. **Technology Stack**
   - **Backend**: FastAPI mounted at `/api/v1`, SQLAlchemy 2.0 (asyncio) ORM, PostgreSQL database (`asyncpg`), Pydantic v2
   - **Frontend**: Single-Page Application (SPA) in `frontend/` using React 19, TypeScript 5.9, Vite 8, Tailwind CSS v4, Dracula dark theme palette, TanStack Query v5, and typed `openapi-fetch`
   - **Authentication**: JWT Bearer tokens with Argon2id password hashing
   - **AI Planning Engine**: Multi-provider LLM client (OpenAI-compatible and Anthropic message formats) with physiological fallback logic and training load analytics (CTL, ATL, TSB)
   - **External Integrations**: Strava OAuth2, webhook push events, and automatic activity reconciliation

2. **Backend Structure (`src/app/`)**
   - `main.py`: FastAPI app initialization, CORS middleware, OpenAPI metadata
   - `core/`: Security utils (Argon2id password hashing, JWT token creation and verification)
   - `api/`: REST API routers
     - `auth.py`: `/myactivities/auth` (`/register`, `/login`)
     - `user.py`: `/myactivities/user` (`/`, `/preferences`, `/activities`, `/strava`)
     - `activities.py`: `/myactivities/activities` (CRUD, metrics, rescheduling)
     - `strava.py`: `/myactivities/strava` (OAuth, on-demand sync, webhook push events)
     - `ai.py`: `/myactivities/ai` (arbitrary horizon planning, plan confirmation, load analytics, weekly recaps)
   - `models/`: Database models (`Activity`, `ActivityMetric`, `WeekPlan`, `TrainingPreference`, `Athlete`)
   - `schemas/`: Pydantic models for validation and responses
   - `services/`: Business logic layer (`activities_service`, `athlete_service`, `auth_service`, `strava_sync_service`)
   - `integrations/`: Third-party clients (Strava API client)
   - `ai/`: Multi-provider AI client, training load analysis (CTL/ATL/TSB), and adaptive planner

3. **Frontend Structure (`frontend/src/`)**
   - `api/`: Configured `openapi-fetch` client with auth interceptor and generated OpenAPI types (`schema.d.ts`)
   - `components/`:
     - `calendar/`: `CalendarStrip` horizontal scrollable week view and day workout cards
     - `chat/`: `AIChatDrawer` conversational coach panel
     - `analytics/`: `TrainingLoadDrawer` CTL/ATL/TSB and readiness visualization
     - `workout/`: `WorkoutModal` and `WorkoutDetailInline` structured workout inspection
     - `settings/`: `SettingsDrawer` profile and training preferences
     - `layout/`: `BottomToolbar` clean navigation bar
     - `auth/`: `AuthScreen` login, register, and quick demo login
   - `context/`: `AuthContext` for JWT token lifecycle and user profile state
   - `hooks/`: `useQueries.ts` wrapping TanStack Query hooks

4. **Database Layer**
   - Single unified `Activity` table for planned, completed, missed, and modified workouts
   - 1:1 `ActivityMetric` table for completed activity telemetry (HR, power, cadence, calories, etc.)
   - Composite DB indexes for high-throughput calendar queries:
     `idx_activities_athlete_planned`, `idx_activities_athlete_actual`, `idx_activities_athlete_status`, `idx_week_plans_athlete_start`

5. **Security & Authorization**
   - Endpoints prioritize authenticated context (`get_current_athlete` / `get_optional_current_athlete`)
   - Prevents unauthenticated IDOR access; athlete UUIDs are inferred from the JWT Bearer token

6. **Development Workflow & Commit Guidelines**
   - **Permission Required**: Always ask the user for explicit permission before executing `git commit` or `git push`.
   - **No Emojis**: Maintain zero emojis across all code, documentation, scripts, and commit messages.
   - **Tests**: Run `pytest` and `cd frontend && npm run build` before asking to commit or push.
   - **Branch**: Work strictly on `feature/dev`.