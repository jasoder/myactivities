# MyActivities Specification

## Overview

Full-stack endurance training app with a FastAPI + PostgreSQL backend and a React 19 + TypeScript SPA (`frontend/`).

## Core Features

- **Authentication**: Email/password registration and login (`POST /myactivities/auth/register`, `/login`) with Argon2id hashing and JWT Bearer tokens.
- **Calendar & Workouts**:
  - Weekly calendar view populated from `GET /myactivities/user/activities`.
  - Create, inspect, reschedule, complete, and delete workouts (`/myactivities/activities`).
  - Marking a planned workout complete keeps it on its original scheduled day.
- **AI Coach & Training Load**:
  - Training load analytics (`GET /myactivities/ai/training-load`) computing CTL, ATL, TSB, and readiness.
  - Adaptive plan preview (`POST /myactivities/ai/generate-plan`, 1–60 days) and confirmation (`POST /myactivities/ai/confirm-plan`).
  - Supports full-week planning, targeted additions (including multiple workouts per day), single-day swaps, and workout removals.
  - Weekly recap (`GET /myactivities/ai/weekly-recap`) comparing planned vs. completed volume.
- **Strava Integration**:
  - OAuth2 connect/disconnect, manual sync (`POST /myactivities/strava/sync`), and webhook ingestion (`GET|POST /myactivities/strava/webhook`).
- **Athlete Settings**:
  - Profile metrics (FTP, threshold pace, weight, max HR, LTHR) and training preferences (preferred sports, weekly hours, max days/week, rest days, split notes).

## Data Model

- `athletes`: User accounts, physiological metrics, preferred sports, Strava tokens.
- `activities`: Unified planned/completed/missed/modified workouts with `planned_date`, `actual_date`, `plan_metadata` (JSONB).
- `activity_metrics`: 1:1 completed workout telemetry (HR, power, distance, duration, calories).
- `week_plans`: Groups AI-generated workout batches.
- `training_preferences`: Per-athlete scheduling constraints.
