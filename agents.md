# Agent guidelines

- The local stack is Docker Compose: Postgres, Django (`:8000`), and Vite (`:5173`). Run `docker compose up --build` (Cloud Agents already start it via `.cursor/start.sh`).
- Application code talks to PostgreSQL. Hermetic Bazel tests set `FOOPLACE_USE_SQLITE=1` so they do not need a running database.
- Always make sure to work in small chunks, always prefer using smaller agents to save money.
- Never change test to pass it
- Always keep the code as simple as possible, think a new engineer will need to understand it
- Install any commands the repo relies on (for example `just`, `rg`, or `cargo-insta`) if they aren't already available before running instructions here.
- When writing tests, prefer comparing the equality of entire objects over fields one by one.
- Do not add tests for values that are statically defined.
- Do not add negative tests for logic that was removed.
- Avoid large modules:
  - Prefer adding new modules instead of growing existing ones.
