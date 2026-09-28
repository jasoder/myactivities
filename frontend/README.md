# MyActivities Frontend

Single-page application (SPA) dashboard for MyActivities, built with React 19, TypeScript, Vite, and Tailwind CSS v4. Designed with a Dracula dark theme color scheme for optimal readability on mobile and desktop devices.

## Features

- **Weekly Calendar Strip**:
  - Horizontal calendar showing the current week, navigable with previous/next controls and touch swiping.
  - Daily cards displaying planned, completed, missed, and modified workout status indicators.
  - Activity badges by sport type (Run, Ride, Swim, WeightTraining, etc.).
- **Structured Workout Detail**:
  - Expandable modal and inline view displaying warmup, interval sets, and cooldown structure.
  - Target metrics (duration, distance, intensity zones) and recorded performance telemetry.
- **Bottom Navigation Toolbar**:
  - Precision docked dock bar providing direct access to AI Chat Coach, Training Load analytics, Add Workout, and Athlete Profile/Preferences.
- **Athlete Profile, Goals & Preferences Drawer**:
  - Training goals configuration: weekly target hours, maximum training days per week, interactive rest day selector, active sports selection, and coaching focus notes.
  - Physiological metrics: Functional Threshold Power (FTP), Weight (kg), Max Heart Rate (bpm), Lactate Threshold Heart Rate (LTHR), and Threshold Pace (min/km).
  - External integrations: Strava OAuth connect, on-demand manual synchronization, and disconnect options.
- **Conversational AI Coach Drawer**:
  - Interactive chat drawer to adjust planned sessions, trigger adaptive weekly plan generation, and ask coaching questions.
- **Training Load and Physiological Readiness Drawer**:
  - Chronic Training Load (CTL / Fitness), Acute Training Load (ATL / Fatigue), and Training Stress Balance (TSB / Form) visualization.
  - Physiological readiness scoring and recovery recommendations.
- **Authentication**:
  - JWT authentication flow with registration, login, quick demo login, and automatic session invalidation on token expiry (HTTP 401).
- **Type-Safe API Client**:
  - Strongly typed client using `openapi-fetch` and `openapi-typescript`.
  - Automatic type generation from the backend FastAPI OpenAPI schema.

## Technology Stack

- **Framework**: React 19 + TypeScript 5.9
- **Build Tool**: Vite 8 with Hot Module Replacement (HMR)
- **Styling**: Tailwind CSS v4 with Dracula palette accents (`#282a36`, `#44475a`, `#bd93f9`, `#50fa7b`, `#ff79c6`, `#8be9fd`, `#ffb86c`, `#ff5555`)
- **Server State**: TanStack React Query v5
- **Networking**: `openapi-fetch`
- **Icons**: Lucide React

## Project Structure

```
frontend/
├── scripts/
│   └── generate-api.js          # Node script to fetch OpenAPI spec and generate schema.d.ts
├── src/
│   ├── api/
│   │   ├── client.ts            # Configured openapi-fetch client with auth interceptor
│   │   └── schema.d.ts          # Auto-generated TypeScript types from backend OpenAPI
│   ├── assets/                  # Static assets and icons
│   ├── components/
│   │   ├── analytics/           # Training load & readiness drawer
│   │   ├── auth/                # Login, registration, and demo auth view
│   │   ├── calendar/            # Calendar strip and day workout cards
│   │   ├── chat/                # AI assistant slide-out drawer
│   │   ├── layout/              # Bottom navigation toolbar
│   │   ├── settings/            # Athlete profile, preferences, and Strava status
│   │   └── workout/             # Structured workout detail modal and inline card
│   ├── context/
│   │   └── AuthContext.tsx      # Auth state provider and token storage
│   ├── hooks/
│   │   └── useQueries.ts        # TanStack query and mutation hooks
│   ├── utils/
│   │   └── date.ts              # Date formatting and week calculation utilities
│   ├── App.tsx                  # Root application component
│   ├── index.css                # Tailwind CSS imports and custom utility styles
│   └── main.tsx                 # React entry point with QueryClientProvider
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## Available Scripts

### `npm install`
Installs all dependencies.

### `npm run dev`
Starts the local development server at `http://localhost:5173`.
Before starting Vite, this automatically runs `npm run api:generate` (via `predev`) to ensure TypeScript types are up to date with the backend.

### `npm run build`
Compiles TypeScript files (`tsc -b`) and generates production bundles into `dist/`.

### `npm run api:generate`
Fetches the live OpenAPI schema from `http://localhost:8000/api/v1/docs/openapi.json` (or the URL specified by `API_DOCS_URL`) and updates `src/api/schema.d.ts`. If the backend is offline, the script falls back gracefully to the existing generated schema file.

### `npm run lint`
Runs Oxlint on frontend source code.

### `npm run preview`
Locally previews the production build from `dist/`.
