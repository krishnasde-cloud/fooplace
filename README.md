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

## Deploy to Vercel

Deploys are **manual**. GitHub Actions does not publish on push.

1. Open **Actions → Deploy to Vercel → Run workflow**.
2. Leave **Deploy to production** checked for the production domain, or uncheck it for a preview URL.
3. Run the workflow. It builds `//frontend:bundle` with Bazel, copies the output out of `bazel-bin` (following symlinks), and uploads `dist/` with the Vercel CLI.

Credentials live in the GitHub Environment **Vercel-prod** (`VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`). The Vercel project is already linked to the Neon production database; this workflow only ships the static React app. Django is not hosted on Vercel.

## Refreshing Python locks

```bash
bazel run //backend:requirements.update
```
