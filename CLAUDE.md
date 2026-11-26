# CLAUDE.md

Guidance for working in this repository.

## Commands

- **Backend tests**: `.venv_ci/bin/pytest` (or `pytest` in active venv)
- **Backend server**: `cd src && uvicorn app.main:app --reload`
- **Frontend dev**: `cd frontend && npm run dev` (`http://localhost:5173`)
- **Frontend build & typecheck**: `cd frontend && npm run build`
- **Regenerate API types**: `cd frontend && npm run api:generate`
- **Docker**: `docker compose up --build -d` / `docker compose down`

## Architecture

- **Backend (`src/app/`)**: FastAPI mounted at `/api/v1` (routers under `/myactivities`: `auth`, `user`, `activities`, `strava`, `ai`), async SQLAlchemy 2.0 + PostgreSQL, Pydantic v2, JWT + Argon2id auth.
- **AI Engine (`src/app/ai/`)**: Multi-provider client (`client.py`) with physiological fallback, CTL/ATL/TSB load analysis (`load_analysis_service.py`), and adaptive planner (`planner_service.py`) supporting full plans, targeted adds, swaps, and removals.
- **Frontend (`frontend/src/`)**: React 19, TypeScript, Vite 8, Tailwind CSS v4 (Dracula theme), TanStack Query v5, `openapi-fetch` (`api/schema.d.ts`).
- **Database**: Unified `activities` table (`planned`, `completed`, `missed`, `modified`), 1:1 `activity_metrics`, `week_plans`, `training_preferences`, `athletes`.

## Rules

- Always ask for explicit permission before `git commit` or `git push`.
- Keep zero emojis across code, docs, and commit messages.
- Run `pytest` and `cd frontend && npm run build` before committing or pushing.
- Work on `feature/dev`.
