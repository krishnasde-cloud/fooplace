# fooplace

Bazel monorepo for Fooplace: a **React 19** frontend and a **Django 6.1** backend.

## Layout

| Path | What |
| --- | --- |
| `frontend/src/app/` | App shell (layout, top-level screens) |
| `frontend/src/modules/` | Feature modules (UI + API client per feature) |
| `frontend/src/shared/` | Cross-module helpers and UI |
| `backend/fooplace/` | Django project config (settings, root URLs) |
| `backend/modules/` | Feature modules (one Django app per folder) |
| `MODULE.bazel` | Bzlmod deps: Bazel 9.2, `aspect_rules_js` 3.4.1, `rules_python` 2.3.2 |

A **module** is one folder that groups a feature on both sides. Backend modules with an `apps.py` are auto-installed and mounted at `/api/<name>/`. Frontend modules live at `frontend/src/modules/<name>/` and import via `@/modules/<name>/…`.

`health` is the example: `GET /api/health/` and `frontend/src/modules/health/`. `clerk` is mounted at `GET /api/me/` so the existing auth contract stays the same.

## Adding a module

Prefer a new module over growing an existing one.

```bash
bazel run //backend:manage -- startmodule places
```

That creates `backend/modules/places/` (views, urls, tests, …) and `frontend/src/modules/places/` (API client). No settings or URL edits are required.

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
bazel run //backend:manage -- startmodule places

# Vite dev server (proxies /api to Django on :8000)
pnpm --filter @fooplace/frontend dev
```

The SPA calls `GET /api/health/`. With both servers running, Vite proxies that path to Django.

## Django admin

`/admin/` is limited to Fooplace users with `type=admin`. Sign in with Clerk (password login stays disabled). New sign-ups stay buyers. After someone has signed in once, promote them:

```bash
bazel run //backend:manage -- promoteadmin you@example.com
```

Locally open http://localhost:5173/admin/ (Vite proxies it) or http://localhost:8000/admin/. On Vercel the same path is routed to Django. The admin back office is where staff approve or reject new sellers, view every listing and order, and flag or remove a seller or listing.

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

Clerk is the only authentication method. The React header signs users in; Django
verifies the Clerk session JWT (`clerk-backend-api`) and rejects password /
session login. `GET /api/health/` and `GET /api/geoapify/autocomplete/` stay
public (so sellers can pick a pickup address before they have a session).
Other `/api/` writes need a valid session token.

### Env vars (Vercel Production + Preview)

Django runs on Vercel, so these are project env vars (not frontend-only):

| Name | Required | Notes |
| --- | --- | --- |
| `VITE_CLERK_PUBLISHABLE_KEY` | Yes | Public key from [Clerk → API keys](https://dashboard.clerk.com/last-active?path=api-keys). Vite inlines `VITE_*` at **build** time (the deploy workflow pulls it from Vercel before Bazel runs). |
| `CLERK_SECRET_KEY` | Yes | Server-only. Django uses this to verify session JWTs. Never expose to the browser. |
| `CLERK_AUTHORIZED_PARTIES` | Already set | Comma-separated frontend origins for the token `azp` claim. Django also allows `VERCEL_URL`, `VERCEL_BRANCH_URL`, `VERCEL_PROJECT_PRODUCTION_URL`, and the request Origin/Host so the production alias matches. Include the Django origin (`http://localhost:8000`) if you sign in on `/admin/`. |
| `CLERK_PUBLISHABLE_KEY` | No | Optional. Django admin login embeds Clerk when this (or `VITE_CLERK_PUBLISHABLE_KEY`) is set. |
| `CLERK_JWT_KEY` | No | Optional PEM public key for networkless JWT verification. |
| `GEOAPIFY_API_KEY` | Yes for seller signup | Server-only. Django uses this to autocomplete and geocode a seller's pickup address. Never expose to the browser. |

Also add your Vercel URL in the Clerk dashboard under **Configure → Domains**.

Locally: `frontend/.env.example` → `frontend/.env.local` and `backend/.env.example` → `backend/.env`. Docker Compose forwards the Clerk vars from the host environment.

## Refreshing Python locks

```bash
bazel run //backend:requirements.update
```
