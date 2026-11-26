# MyActivities

Full-stack endurance training tracker with Strava sync and an AI adaptive coach.

## Stack

- **Backend**: FastAPI (`/api/v1`), SQLAlchemy 2.0 (async), PostgreSQL 14, JWT + Argon2id
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS v4, TanStack Query, `openapi-fetch`
- **AI Engine**: OpenAI-compatible or Anthropic LLM client with built-in physiological fallback

## Quick Start (Docker)

```bash
docker compose up --build -d
```

- API & Swagger docs: `http://localhost:8000/api/v1/docs`
- Stop containers: `docker compose down`
- PostgreSQL shell: `docker compose exec db psql -U postgres -d myactivities-test`

## Local Development

### Backend

```bash
pip install -r requirements.txt
python -m src.app.db.manage
cd src && uvicorn app.main:app --reload
```

Run tests:

```bash
pytest
```

### Frontend

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173 (auto-syncs OpenAPI types)
npm run build    # Type-check and production build
```

## Project Structure

```
├── frontend/src/        # React SPA (api, components, context, hooks, utils)
├── src/app/
│   ├── api/routers/     # auth, user, activities, strava, ai
│   ├── ai/              # LLM client, adaptive planner, CTL/ATL/TSB load analysis
│   ├── core/            # Security (JWT, Argon2id)
│   ├── db/              # Async SQLAlchemy session & init
│   ├── integrations/    # Strava API client
│   ├── models/          # Athlete, Activity, ActivityMetric, WeekPlan, TrainingPreference
│   ├── schemas/         # Pydantic v2 schemas
│   └── services/        # Business logic & Strava sync
└── tests/               # Pytest suite
```

## API Endpoints (`/api/v1/myactivities`)

- **Auth (`/auth`)**: `POST /register`, `POST /login`
- **User (`/user`)**: `GET|PUT|DELETE /`, `DELETE /strava`, `GET|PUT /preferences`, `GET /activities`
- **Activities (`/activities`)**: `POST /`, `GET /detail/{id}`, `PUT|DELETE /{id}`
- **Strava (`/strava`)**: `GET /auth-url`, `POST /oauth/callback`, `POST /sync`, `GET|POST /webhook`
- **AI Coach (`/ai`)**: `GET /training-load`, `POST /generate-plan`, `POST /confirm-plan`, `GET /weekly-recap`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:myactivities@db:5432/myactivities-test` | Async PostgreSQL URL |
| `SECRET_KEY` | `dev-secret-key-change-in-production` | JWT signing key |
| `STRAVA_CLIENT_ID` | - | Strava OAuth client ID |
| `STRAVA_CLIENT_SECRET` | - | Strava OAuth client secret |
| `STRAVA_VERIFY_TOKEN` | `STRAVA_WEBHOOK_VERIFY_TOKEN` | Strava webhook verify token |
| `AI_API_URL` | - | OpenAI-compatible or Anthropic endpoint |
| `AI_API_KEY` | - | AI provider API key |
| `AI_MODEL` | - | AI model name |
| `ALLOWED_ORIGINS` | `http://localhost:5173,...` | Comma-separated CORS origins |

## License

MIT
