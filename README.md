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

- `/myactivities/athletes` - Athlete management
- `/myactivities/completedActivities` - Completed activities
- `/myactivities/plannedActivities` - Planned activities
- `/myactivities/activities` - Combined activities view
- `/myactivities/strava` - Strava integration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:myactivities@db:5432/myactivities-test` | Database connection string |
| `STRAVA_CLIENT_ID` | - | Strava OAuth client ID |
| `STRAVA_CLIENT_SECRET` | - | Strava OAuth client secret |

## License

MIT