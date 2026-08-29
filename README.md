# fooplace

A tiny full-stack app for saving and browsing places worth remembering.

- **`server/`** — Express + TypeScript JSON API with an in-memory place store.
- **`web/`** — Vite + React + TypeScript UI for adding, listing, and deleting places.

The two workspaces are managed with npm workspaces from the repository root.

## Prerequisites

- Node.js >= 20 (developed against Node 22)
- npm >= 10

## Getting started

```bash
npm install      # install all workspace dependencies
npm run dev       # start the API (:3001) and web dev server (:5173) together
```

Then open http://localhost:5173. The Vite dev server proxies `/api/*` requests to
the API at http://localhost:3001, so no CORS or extra config is needed in dev.

## Common commands

| Command | What it does |
| --- | --- |
| `npm run dev` | Run API and web dev servers concurrently |
| `npm run dev:server` | Run only the API (`tsx watch`) |
| `npm run dev:web` | Run only the web dev server (Vite) |
| `npm test` | Run the API test suite (Vitest + Supertest) |
| `npm run lint` | Lint all workspaces with ESLint |
| `npm run typecheck` | Type-check both workspaces |
| `npm run build` | Compile the API and build the web production bundle |

## API

Base URL: `http://localhost:3001`

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/health` | Health check |
| `GET` | `/api/places` | List places (newest first) |
| `GET` | `/api/places/:id` | Fetch a single place |
| `POST` | `/api/places` | Create a place (`{ name, category?, note? }`) |
| `DELETE` | `/api/places/:id` | Delete a place |

## Cloud Agent environment

`.cursor/environment.json` configures the Cloud Agent dev environment:

- `install`: `npm install`
- `terminals`: `api` and `web` dev servers
- `ports`: 3001 (API) and 5173 (web)
