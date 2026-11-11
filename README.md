# AgentFleet

A self-hostable platform for building, executing and monitoring reliable AI workflows.
First application: autonomous software incident investigation.

## Why
AI agents can do useful work, but running them in real applications raises hard problems:
workflows take minutes or hours, agents fail or return invalid results, tasks depend on each other,
restarts must not destroy progress, tool access must be controlled, and cost and quality must be measured.
AgentFleet is a backend orchestration system built around those problems.

## Focus areas
1. **Durable execution:** workflows survive restarts, failures, retries and worker crashes.
2. **Agent observability:** inspect every decision, tool call, input, output, token cost and event.
3. **Reliability and safety:** idempotency, permission boundaries, approvals, audit trails, recovery.
4. **Evaluation:** replay standardized incidents and measure whether agents find the correct cause.

## Status
Phase 0 is complete and released as `v0.1.0`. Phase 1 (workflow runs and state machines) is in progress.

| Capability | Status |
|---|---|
| Workflow templates API with validated, cycle-free task graphs | Built |
| Runs, task dependencies and enforced state machines | Phase 1 (in progress) |
| Workers executing tasks with safe concurrent claiming | Phase 2 |
| Crash recovery, retries and idempotency | Phase 3 |
| LLM agents with allowlisted tools; incident investigation workflow | Phase 4 |
| Authentication, workspace isolation, human approval | Phase 5 |
| Live event stream and operator UI | Phase 6 |
| Public deployment | Phase 7 |
| Evaluation harness and performance report | Phases 8-9 |

Scope, order and progress are tracked in [`docs/roadmap.md`](docs/roadmap.md).

## Engineering practices
- **Protected `main`.** Every change arrives through a pull request that must pass CI: lint, strict type
  checks, migrations on an empty database, a model/migration drift check, and tests with a coverage gate.
- **Tests on a real PostgreSQL**, including concurrent requests racing for one row, constraint violations
  attempted with raw SQL, and transaction rollback.
- **The database is the last line of defence.** Uniqueness, allowed states and referential integrity are
  constraints, not conventions in application code.
- **Decisions are written down.** Each architectural decision has an [ADR](docs/decisions/) with the
  alternatives considered; core subsystems get a [design doc](docs/design-docs/) before they are built.
- **A build record.** Every slice of work has a [note](docs/slices/) on what was built, how it works and why.

## Documentation
- [Architecture overview](docs/architecture/README.md): layers, request flow, data model, guarantees
- [Roadmap](docs/roadmap.md): phases, slices, exit criteria and progress
- [Architecture decision records](docs/decisions/) and [design docs](docs/design-docs/)
- [Build notes](docs/slices/): a step-by-step record of how each piece was built
- [Technology guide](docs/technology-guide.md): what each technology is and why it was chosen
- [Contributing and delivery workflow](CONTRIBUTING.md) and [changelog](CHANGELOG.md)
- [Product brief](docs/product-brief.md) and [UI design direction](docs/ui-design/README.md)

## Local development
Requirements: Docker, [uv](https://docs.astral.sh/uv/) (it installs Python 3.12 if needed) and GNU Make.

```bash
make setup    # create .env (gitignored) and install locked dependencies
make up       # start PostgreSQL 17 on host port 5433
make run      # apply migrations and start the API with auto-reload
```

The API is then at http://localhost:8000, with interactive OpenAPI docs at http://localhost:8000/docs.

```bash
make check    # everything CI runs: lint, format, types, migrations, drift check, tests + coverage
make help     # list all commands
```

Changes reach `main` only through pull requests that pass CI. The workflow is described in
[CONTRIBUTING.md](CONTRIBUTING.md), and releases are listed in [CHANGELOG.md](CHANGELOG.md).

## License
[MIT](LICENSE)

_A full README (screenshots, architecture diagram, demo link, limitations) will replace this once the
product is further along._
