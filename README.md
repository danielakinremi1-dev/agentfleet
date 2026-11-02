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
Early development. Progress is tracked in the table at the top of [`docs/roadmap.md`](docs/roadmap.md).

## Documentation
- [Product brief](docs/product-brief.md)
- [Roadmap](docs/roadmap.md)
- [Technology guide](docs/technology-guide.md): what each technology is and why it was chosen
- [Architecture decision records](docs/decisions/)
- [Build notes](docs/slices/): a step-by-step record of how each piece was built
- [Design direction](docs/design/README.md)

## Local development
Requirements: Docker, [uv](https://docs.astral.sh/uv/) (it installs Python 3.12 if needed).

```bash
cp .env.example .env           # local defaults; .env is gitignored
docker compose up -d db        # PostgreSQL 17 on host port 5433
cd backend
uv sync                        # install locked dependencies
uv run alembic upgrade head    # create the schema
uv run uvicorn app.main:app --reload
```

The API is then at http://localhost:8000, with interactive OpenAPI docs at http://localhost:8000/docs.

Checks (the same ones CI runs):

```bash
uv run ruff check . && uv run ruff format --check . && uv run mypy
uv run pytest                  # runs against a real PostgreSQL test database
```

_A full README (screenshots, architecture diagram, demo link, limitations) will replace this once the
product is further along._
