# MyActivities API

A FastAPI backend for tracking athlete activities with Strava integration.

## Architecture

- **FastAPI** - Modern, fast web framework
- **SQLAlchemy** - Async ORM for database operations
- **PostgreSQL** - Primary database
- **Docker** - Containerized database
- **React** - Frontend (separate repo)

## Quick Start

### Prerequisites
- Python 3.11+
- Docker (for PostgreSQL)
- Virtual environment recommended

### Setup

1. **Clone and navigate to project:**
   ```bash
   cd myactivities
   ```

2. **Start PostgreSQL via Docker (creates postgres superuser automatically):**
   ```bash
   # Stop any existing container
   docker stop pg-db 2>/dev/null || true
   docker rm pg-db 2>/dev/null || true
   
   # Start fresh container with proper initialization
   docker run -d \
     -e POSTGRES_USER=postgres \
     -e POSTGRES_PASSWORD=myactivities \
     -e POSTGRES_DB=myactivities-test \
     -p 5432:5432 \
     --name pg-db \
     postgres:18
   
   # Wait for PostgreSQL to fully initialize
   sleep 5
   ```

3. **Verify database roles are created (run these to confirm):**
   ```bash
   docker exec pg-db psql -U postgres -c "\du"
   ```

4. **Activate virtual environment and install dependencies:**
   ```bash
   source .venv_ci/bin/activate
   pip install -r requirements.txt
   ```

5. **Run database migrations (creates tables):**
   ```bash
   python -m src.scripts.init_db
   ```

6. **Start the development server:**
   ```bash
   cd src
   source ../.venv_ci/bin/activate
   uvicorn app.main:app --reload
   ```

7. **Verify the server is running:**
   - Open http://127.0.0.1:8000 in browser
   - API docs available at http://127.0.0.1:8000/docs

### Running Tests

```bash
source .venv_ci/bin/activate
pytest -v
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
│   │   ├── session.py       # Database session management
│   │   ├── base.py          # SQLAlchemy base
│   │   └── manage.py        # Database management
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   └── integrations/        # External integrations (Strava)
├── scripts/
│   ├── init_db.py           # Database initialization
│   └── seed_db.py           # Seed data
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
| `DATABASE_URL` | `postgresql+psycopg2://myactivities:myactivities@localhost:5432/myactivities-test` | Database connection string |
| `STRAVA_CLIENT_ID` | - | Strava OAuth client ID |
| `STRAVA_CLIENT_SECRET` | - | Strava OAuth client secret |

### Docker Compose (Alternative)

```yaml
version: '3.8'
services:
  db:
    image: postgres:18
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: myactivities
      POSTGRES_DB: myactivities-test
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

Run with: `docker-compose up -d`

## License

MIT