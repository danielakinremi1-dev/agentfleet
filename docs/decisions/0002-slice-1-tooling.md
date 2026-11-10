# ADR-0002: Slice 1 tooling

Status: accepted

## Context
The project needs a foundation that supports async API and worker code and produces trustworthy tests.

## Decision
1. **`uv`** for dependency management and lockfile.
2. **Async SQLAlchemy 2.0 with `asyncpg`**, because the API and workers both run on asyncio.
3. **PostgreSQL in Docker Compose.** The API runs locally during development for fast reload; the worker
   joins Compose in Phase 2.
4. **`ruff`, `mypy` and `pytest`** from the first commit. Tests run against a real PostgreSQL.

## Alternatives considered
- **Sync SQLAlchemy with threads:** simpler to reason about, but inconsistent with the asyncio worker design.
- **pip or Poetry:** workable, but slower or less standard for new projects.
- **SQLite for tests:** faster, but row-locking (`FOR UPDATE SKIP LOCKED`) and concurrency behave differently,
  so it would hide the failures that matter most for this system.

## Consequences
- Relationships cannot be lazy-loaded implicitly in async sessions; loading strategy is explicit.
- Tests need a running PostgreSQL (Compose locally, a service container in CI).
- Details for each technology are in `docs/technology-guide.md`.
