# Changelog

Notable changes to AgentFleet. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Each completed roadmap phase is a release (see [CONTRIBUTING.md](CONTRIBUTING.md#releases)).

## [Unreleased]

### Added
- MIT license.
- Dependency graph validation: cyclic workflow templates are rejected with a `422` that names the cycle.
- Design doc 0001 (run lifecycle) and ADR-0008 (dependency graph validation).
- Workflow runs: `POST /api/workflows/{id}/runs` creates a run with one task per template task and its
  dependencies, atomically; `GET /api/runs/{id}` returns the run with its task graph; `GET /api/runs`
  lists runs.
- Migration `0002`: the `task_dependencies` table and `tasks.position`.
- ADR-0009 (run materialization).

### Changed
- A task that lists the same dependency more than once is now rejected (`422`).
- Validation error responses (`422`) no longer include the rejected value (`input`).

### Fixed
- A request body containing `NaN` returned `500` instead of `422`.
- A NUL character in a template name, description or task name returned `500` instead of `422`.

## [0.1.0] - 2026-11-10

Phase 0: foundation.

### Added
- Backend project scaffold: uv project, FastAPI application factory, typed settings, async SQLAlchemy
  engine and per-request sessions.
- Initial schema and migration: `workflow_templates`, `workflow_runs` and `tasks`, with UUID keys,
  CHECK-constrained status columns and JSONB template definitions.
- Endpoints: `GET /health`, `GET /health/ready`, `POST /api/workflows`, `GET /api/workflows`,
  `GET /api/workflows/{id}`.
- Template definition validation: unique task keys, known dependencies, no self-dependencies, size limits.
- Test suite against a real PostgreSQL database, including concurrent-create, constraint,
  rollback and migration round-trip tests.
- Docker Compose service for PostgreSQL 17.
- CI pipeline: lint, format, strict type checks, migrations, model/migration drift check, tests.
- Makefile with one target per developer task; CI runs the same targets.
- Branch coverage measurement with a 90% gate in CI.
- Pull request template, Dependabot configuration, contributing guide and this changelog.
- Branch protection on `main`: pull requests and a passing CI check are required.
- Roadmap restructured into phased slices with exit criteria; architecture overview; design-doc process.
