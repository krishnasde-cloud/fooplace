# fooplace

Bazel monorepo for Fooplace: a **React 19** frontend and a **Django 6.1** backend.

## Layout

| Path | What |
| --- | --- |
| `frontend/` | Vite + React + TypeScript SPA |
| `backend/` | Django project (`fooplace`) with an `api` app |
| `MODULE.bazel` | Bzlmod deps: Bazel 9.2, `aspect_rules_js` 3.4.1, `rules_python` 2.3.2 |

## Prerequisites

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

## Clerk auth

Clerk is the only authentication method. The React header signs users in; Django
verifies the Clerk session JWT and rejects password / session login.

Copy `frontend/.env.example` → `frontend/.env.local` and `backend/.env.example`
→ `backend/.env` for local keys.

### Env vars

| Name | Where | Required | Notes |
| --- | --- | --- | --- |
| `VITE_CLERK_PUBLISHABLE_KEY` | Vercel (Production + Preview) and local Vite | Yes | Public key from [Clerk → API keys](https://dashboard.clerk.com/last-active?path=api-keys). Vite bakes `VITE_*` in at **build** time. |
| `CLERK_SECRET_KEY` | Django host (not the static Vercel SPA) | Yes for API auth | Server-only. Never expose to the browser. |
| `CLERK_JWT_KEY` | Django host | No | Optional PEM public key for networkless JWT verification. |
| `CLERK_AUTHORIZED_PARTIES` | Django host | Recommended in prod | Comma-separated frontend origins (your Vercel URL). Defaults to local Vite. |

Also add your Vercel URL in the Clerk dashboard under **Configure → Domains**.

## Refreshing Python locks

```bash
bazel run //backend:requirements.update
```
