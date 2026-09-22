# MyActivities API

A FastAPI backend for tracking athlete activities with Strava integration.

## Architecture

- **FastAPI** - Modern, fast web framework
- **SQLAlchemy** - Async ORM for database operations
- **PostgreSQL** - Primary database
- **Docker** - Containerized database and application
- **React** - Frontend (separate repo)

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ (for local development only)

### Run with Docker Compose (Recommended)

This starts PostgreSQL, initializes the database schema, and runs the API in a single command:

```bash
docker compose up --build -d
```

The API will be available at `http://localhost:8000` (docs at `/docs`).

To run in the background:

```bash
docker compose up -d
```

To stop and remove the containers (the database volume persists):

```bash
docker compose down
```

### Local Development (without Docker)

If you prefer to run locally:

1. **Start PostgreSQL:**
   ```bash
   docker run -d \
     -e POSTGRES_USER=postgres \
     -e POSTGRES_PASSWORD=myactivities \
     -e POSTGRES_DB=myactivities-test \
     -p 5432:5432 \
     --name pg-db \
     postgres:14
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database:**
   ```bash
   python -m src.app.db.manage
   ```

4. **Start the development server:**
   ```bash
   cd src
   uvicorn app.main:app --reload
   ```

### Running Tests

```bash
pytest
```

### Project Structure

```
src/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── api/
│   │   ├── api_router.py    # Main router
│   │   └── routers/         # API endpoints
│   ├── db/
│   │   ├── base.py          # SQLAlchemy base
│   │   └── manage.py        # Database initialization
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   └── integrations/        # External integrations (Strava)
```

### API Endpoints

All endpoints are mounted under root path `/api/v1` and versioned under prefix `/myactivities`.
Interactive Swagger UI documentation is available at `/api/v1/docs` (OpenAPI JSON at `/api/v1/docs/openapi.json`).

- **Authentication (`/myactivities/auth`)**:
  - `POST /register` - Register a new athlete account (email & password)
  - `POST /login` - Authenticate and obtain a JWT Bearer access token

- **User Self-Service (`/myactivities/user`)**:
  - `GET /` - Fetch currently authenticated user profile
  - `PUT /` - Update user profile (name, timezone, performance metrics, sports)
  - `DELETE /` - Delete account and all associated data
  - `DELETE /strava` - Disconnect Strava integration
  - `GET /preferences` - Get athlete training preferences (rest days, weekly target hours)
  - `PUT /preferences` - Update athlete training preferences
  - `GET /activities` - Fetch calendar activities for date range (`start_date` to `end_date`)

- **Activities CRUD (`/myactivities/activities`)**:
  - `POST /` - Create a new planned or completed activity
  - `GET /detail/{activity_id}` - Retrieve activity details with 1:1 metrics
  - `PUT /{activity_id}` - Update activity (status, date rescheduling, comments)
  - `DELETE /{activity_id}` - Delete an activity

- **Strava Integration (`/myactivities/strava`)**:
  - `GET /auth-url` - Generate Strava OAuth authorization URL
  - `POST /oauth/callback` - Handle OAuth exchange code
  - `POST /sync` - Trigger sync of athlete Strava activities
  - `GET /webhook` - Webhook verification endpoint (Strava hub challenge)
  - `POST /webhook` - Webhook push event ingestion and automated sync

- **AI Adaptive Scheduling (`/myactivities/ai`)**:
  - `GET /training-load` - Calculate historical training load (CTL, ATL, TSB, fatigue)
  - `POST /generate-plan` - Preview an AI adaptive training plan (1 to 60 days)
  - `POST /confirm-plan` - Confirm and schedule the generated workouts to the calendar
  - `GET /weekly-recap` - Retrospective morning report / weekly summary comparing planned vs completed

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:myactivities@db:5432/myactivities-test` | Database connection string |
| `SECRET_KEY` | `dev-secret-key-change-in-production` | Secret key for JWT signing |
| `STRAVA_CLIENT_ID` | - | Strava OAuth client ID |
| `STRAVA_CLIENT_SECRET` | - | Strava OAuth client secret |
| `STRAVA_VERIFY_TOKEN` | `STRAVA_WEBHOOK_VERIFY_TOKEN` | Verification token for Strava webhooks |
| `AI_API_URL` | - | URL for AI service (OpenAI-compatible or Anthropic endpoint) |
| `AI_API_KEY` | - | API key for AI provider |
| `AI_MODEL` | - | Model identifier for AI completions |
| `ALLOWED_ORIGINS` | `http://localhost:5173,...` | Allowed CORS origins (comma-separated) |

## License

MIT