# MyActivities Frontend

React 19 + TypeScript + Vite SPA with Tailwind CSS v4 (Dracula palette), TanStack Query v5, and `openapi-fetch`.

## Features

- **Calendar Strip**: Horizontal week view with swipe navigation and status indicators (`planned`, `completed`, `missed`, `modified`).
- **Workout Views**: Create modal and expandable inline detail card with warmup/sets/cooldown structure and status/date controls.
- **AI Coach Drawer**: Chat interface to generate plans, add/swap sessions, or remove workouts with preview and confirmation.
- **Training Load Drawer**: CTL, ATL, TSB, readiness score, and weekly recap.
- **Settings Drawer**: Profile metrics, training preferences, and Strava connection/sync.

## Structure

```
frontend/
├── scripts/generate-api.js    # Fetches OpenAPI JSON into src/api/schema.d.ts
└── src/
    ├── api/                   # openapi-fetch client + generated types
    ├── components/            # analytics, auth, calendar, chat, layout, settings, workout
    ├── context/               # AuthContext (JWT session)
    ├── hooks/                 # TanStack Query hooks (useQueries.ts)
    └── utils/                 # Date helpers
```

## Scripts

```bash
npm install
npm run dev           # Start dev server at http://localhost:5173 (runs api:generate first)
npm run build         # Type-check and build dist/
npm run api:generate  # Refresh src/api/schema.d.ts from backend OpenAPI
npm run lint          # Run oxlint
```
