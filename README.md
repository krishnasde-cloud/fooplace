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

`health` is the example: `GET /api/health/` and `frontend/src/modules/health/`.

## Adding a module

Prefer a new module over growing an existing one.

```bash
bazel run //backend:manage -- startmodule places
```

That creates `backend/modules/places/` (views, urls, tests, …) and `frontend/src/modules/places/` (API client). No settings or URL edits are required.

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
bazel run //backend:manage -- startmodule places

# Vite dev server (proxies /api to Django on :8000)
pnpm --filter @fooplace/frontend dev
```

The SPA calls `GET /api/health/`. With both servers running, Vite proxies that path to Django.

## Refreshing Python locks

```bash
bazel run //backend:requirements.update
```
