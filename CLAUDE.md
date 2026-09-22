# CLAUDE.md

This file provides guidance when working with code in this repository.

**Common Development Commands:**
- **Install dependencies**: `pip install -r requirements.txt`
- **Start server**: `cd src && uvicorn app.main:app --reload`
- **Run test suite**: `pytest`
- **Run specific test**: `pytest tests/test_user.py`
- **Run with Docker Compose**: `docker compose up --build -d`

**Code Architecture Overview:**
1. **Technology Stack**
   - FastAPI backend mounted at `/api/v1`
   - SQLAlchemy (asyncio) ORM with PostgreSQL database (`asyncpg`)
   - JWT authentication (`pyjwt`, `argon2-cffi`)
   - Adaptive AI planning engine (`httpx`, multi-provider LLM support)
   - Dockerized development environment

2. **Core Structure (`src/app/`)**
   - `main.py`: FastAPI app initialization, CORS middleware, OpenAPI metadata
   - `core/`: Security utils (argon2 password hashing, JWT token creation/verification)
   - `api/`: REST API routers
     - `auth.py`: `/myactivities/auth` (`/register`, `/login`)
     - `user.py`: `/myactivities/user` (`/`, `/preferences`, `/activities`, `/strava`)
     - `activities.py`: `/myactivities/activities` (CRUD, metrics, rescheduling)
     - `strava.py`: `/myactivities/strava` (OAuth, on-demand sync, webhook push events)
     - `ai.py`: `/myactivities/ai` (arbitrary duration planning, confirmation, load analytics, recaps)
   - `models/`: Database models (`Activity`, `ActivityMetric`, `WeekPlan`, `TrainingPreference`, `Athlete`)
   - `schemas/`: Pydantic models for validation and responses
   - `services/`: Business logic layer (`activities_service`, `athlete_service`, `auth_service`, `strava_sync_service`)
   - `integrations/`: Third-party clients (Strava API)
   - `ai/`: Multi-provider AI client, training load analysis (CTL/ATL/TSB), and adaptive planner

3. **Database Layer**
   - Single unified `Activity` table for planned, completed, missed, and modified workouts
   - 1:1 `ActivityMetric` table for completed activity telemetry
   - Composite DB indexes for high-throughput calendar queries:
     `idx_activities_athlete_planned`, `idx_activities_athlete_actual`, `idx_activities_athlete_status`, `idx_week_plans_athlete_start`

4. **Security & Authorization**
   - Endpoints prioritize authenticated context (`get_current_athlete` / `get_optional_current_athlete`)
   - Prevents unauthenticated IDOR access; athlete UUIDs are inferred from the JWT Bearer token

5. **Development Workflow & Testing**
   - All tests run via `pytest` (standard async tests using in-memory or test databases)
   - Keep git history clean with focused, atomic commits
   - Always run the test suite to ensure green CI before pushing changes