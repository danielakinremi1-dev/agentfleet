# ADR-0005: Test database strategy

Status: accepted

## Context
Tests must run against a real PostgreSQL (ADR-0002): locking, constraint and concurrency behaviour is what
this system depends on. Tests need isolation from each other and from development data, must work locally and
in CI, and later slices add tests where several connections (workers) compete for the same rows.

## Decision
1. **A separate test database**, `agentfleet_test` (`TEST_DATABASE_URL`), created automatically on first run.
   Development data in `agentfleet` is never touched.
2. **The schema is built by running the Alembic migrations** (`upgrade head`) once per test session, so every
   test run exercises the real migrations rather than `metadata.create_all()`.
3. **Tables are truncated before each test**, and tests commit for real. Truncating before rather than after
   means an interrupted earlier run cannot leak state into the next.
4. **Each test gets its own engine and app lifespan**, created and disposed inside that test's event loop, which
   avoids sharing connections across event loops.
5. **Migration tests** downgrade to base and upgrade again, and `alembic check` verifies models and migrations
   agree. CI also runs `alembic upgrade head` and `alembic check` as separate steps.

## Alternatives considered
- **Wrap each test in a rolled-back transaction (savepoint recipe):** faster, but data is visible only on the
  test's own connection, so it cannot test concurrent claims across connections, and it hides commit-related
  bugs.
- **A fresh database per test (template databases):** strongest isolation, noticeably slower.
- **Testcontainers:** self-contained, but adds a dependency and container start-up time on every run;
  Compose locally and a service container in CI already provide PostgreSQL.

## Consequences
- Tests cannot run in parallel against one database without further work (for example a database per worker
  with `pytest-xdist`).
- A test that needs data must create it itself; nothing persists between tests.
