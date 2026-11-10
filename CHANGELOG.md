# Changelog

Notable changes to AgentFleet. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Each completed roadmap phase is a release (see [CONTRIBUTING.md](CONTRIBUTING.md#releases)).

## [Unreleased]

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
