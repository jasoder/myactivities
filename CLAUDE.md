# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Common Development Commands:**
- 🛠️ **Install dependencies**: `pip install -r requirements.txt`
- ▶️ **Start server**: `uvicorn main:app --reload`
- 🧪 **Run tests**: `pytest`
- 📋 **Run specific test**: `pytest tests/unit/test_*.py` (replace * with specific test file name)
- 🧹 **Lint code**: (No explicit linter configured in project; consider adding pycodestyle/flake8 if needed)

**Code Architecture Overview:**
1. **Technology Stack**
   - FastAPI backend with `/api/v1` routing
   - SQLAlchemy ORM with PostgreSQL database
   - Dockerized environment
   - React frontend (implied by tech stack)

2. **Core Structure**
   - `src/app/`: Contains main application logic
     - `main.py`: Initializes FastAPI app with routers
     - `api/`: RESTful API routes organized in routers
     - `models/`: Database models (icu_activity, completed_activity, planned_activity, athlete)
     - `schemas/`: Pydantic models for request/response
     - `services/`: Business logic/services
     - `integrations/`: Third-party integrations (Strava)

3. **Database Layer**
   - `src/app/db/`: SQLAlchemy base class and session management
   - Database schema managed via migrations (not explicitly shown in current files)

4. **Key Features**
   - Athlete activity tracking with CRUD operations
   - Strava integration for activity sync
   - Modular API design with clear resource separation

5. **Development Workflow**
   - API endpoints are versioned under `/myactivities/`
   - Services handle business logic while models handle data structures
   - Test coverage appears minimal based on current file structure

This structure allows for scalable development with clear separation of concerns. New features should follow the existing pattern of adding routes in `api/`, models in `models/`, and services in `services/`.