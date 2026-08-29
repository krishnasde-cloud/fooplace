# fooplace

Bazel monorepo for Fooplace: a **React 19** frontend and a **Django 6.1** backend.

## Layout

| Path | What |
| --- | --- |
| `frontend/` | Vite + React + TypeScript SPA |
| `backend/` | Django project (`fooplace`) with an `api` app |
| `MODULE.bazel` | Bzlmod deps: Bazel 9.2, `aspect_rules_js` 3.4.1, `rules_python` 2.3.2 |

## Local Docker environment

Postgres, Django, and the Vite frontend run together:

```bash
docker compose up --build
```

| Service | URL |
| --- | --- |
| Frontend (Vite) | http://localhost:5173 |
| Backend (Django) | http://localhost:8000/api/health/ |
| Postgres | `localhost:5432` (user/password/db: `fooplace`) |

The app uses **PostgreSQL**. Cursor Cloud Agents start this same stack from `.cursor/environment.json`. Deployment databases (for example Neon) are configured separately.

Copy `.env.example` to `.env` only if you want to override the defaults.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose (for the local stack above)
- [Bazelisk](https://github.com/bazelbuild/bazelisk) (pins Bazel **9.2.0** via `.bazelversion`)
- Optional for local JS iteration: Node.js 22+ and [pnpm 10.34.5](https://pnpm.io/)

## Common commands

```bash
# Install JS deps (updates pnpm-lock.yaml when package.json changes)
pnpm install

# Build the React production bundle
bazel build //frontend:bundle

# Run Django unit tests
bazel test //backend:test

# Django management commands (runserver, migrate, …)
bazel run //backend:manage -- migrate
bazel run //backend:manage -- runserver 0.0.0.0:8000

# Vite dev server (proxies /api to Django on :8000)
pnpm --filter @fooplace/frontend dev
```

The SPA calls `GET /api/health/`. With both servers running, Vite proxies that path to Django.

## Deploy to Vercel

Deploys are **manual**. GitHub Actions does not publish on push.

1. Open **Actions → Deploy to Vercel → Run workflow**.
2. Leave **Deploy to production** checked for the production domain, or uncheck it for a preview URL.
3. Run the workflow. It:
   - pulls Vercel env (Neon `DATABASE_URL`, `VITE_CLERK_PUBLISHABLE_KEY`)
   - writes `frontend/.env.production` so Vite can inline the Clerk publishable key
   - builds `//frontend:bundle` and copies it to `public/` (SPA at `/`)
   - on production, runs `bazel run //backend:manage -- migrate --noinput`
   - deploys Django as a Vercel Function at `api/index.py` (SPA stays in `public/`)

After changing Vercel env vars, re-run this workflow. Vite cannot read keys that were added only after the frontend was already built.

Credentials live in the GitHub Environment **Vercel-prod** (`VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`). The Vercel project is already linked to the Neon production database. Django reads `DATABASE_URL` (Neon on Vercel; local Docker Compose Postgres). Bazel tests can use SQLite via `FOOPLACE_USE_SQLITE=1`.

## Clerk auth

Sign-in lives in the React header (`frontend/src/AuthHeader.tsx`). Copy `frontend/.env.example` to `frontend/.env.local` for local keys.

### Env vars to add on Vercel

| Name | Required | Notes |
| --- | --- | --- |
| `VITE_CLERK_PUBLISHABLE_KEY` | Yes | Public key from [Clerk → API keys](https://dashboard.clerk.com/last-active?path=api-keys). Vite bakes this in at **build** time (the deploy workflow pulls it from Vercel before Bazel runs). |
| `CLERK_SECRET_KEY` | No | Server-only. Skip on Vercel for this static frontend. Add later if Django should verify Clerk JWTs. |

Also add your Vercel URL in the Clerk dashboard under **Configure → Domains**.

## Refreshing Python locks

```bash
bazel run //backend:requirements.update
```
