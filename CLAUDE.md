# AgentFleet: contributor guide

## What this project is
A self-hostable platform for building, executing and monitoring reliable AI workflows.
First application: autonomous software incident investigation.
Every subsystem should be demoable live and explainable from first principles, and every
engineering decision should be recorded with its rationale.

Before starting a task, read `docs/roadmap.md` and the latest file in `docs/slices/`.
Consult `docs/product-brief.md`, `docs/technology-guide.md` and `docs/decisions/` when relevant
to the task. If a `CLAUDE.local.md` exists, follow it as well.

## Development process
1. **Work in small slices** (about 2-4 hours each). Branch per slice: `slice/<n>-<name>`.
   Each slice ends with a pull request. Do not merge to `main`; the owner reviews and merges.
2. **Decide, build, then ask.** Make reasonable default decisions guided by the architecture
   principles below and keep moving; do not stop mid-slice to wait for approval. Record each
   decision as it is made. At the end of the slice, list the uncertain choices (default chosen
   and the alternative) in the PR description or reply, not in the docs. Refactor and update the
   docs once they are answered.
   **Always stop and ask first** before anything destructive or irreversible (deleting data or
   branches, force-push, rewriting history, changing repo visibility), anything involving secrets
   or credentials, and adding paid services.
3. **Tests with every slice.** Durability features need failure-injection tests (crash mid-task,
   duplicate delivery, lease expiry).
4. **Review honestly.** Flag risks, scope creep and weak spots in proposed designs.
5. **Prefer readable over clever.** No large unexplained generated modules. If something is hard
   to explain, simplify it. Code comments explain *why*, not *what*.

## Documentation duties
The docs are a step-by-step record of how the system was built and why.

- **`docs/slices/NN-name.md`**: one file per finished slice. What was built, how it works, why it
  was done this way, technologies used, tests, and follow-ups. Use the template in
  `docs/slices/README.md`.
- **`docs/technology-guide.md`**: add or update an entry whenever a technology is introduced
  (what it is, why it was chosen, alternatives, where it is used, trade-offs).
- **`docs/decisions/`**: an ADR for every architectural decision (schema design, job claiming,
  retry policy, auth model, event delivery, and so on). Number sequentially.
- **Voice:** professional engineering documentation. State what was chosen and why, with
  alternatives and trade-offs, in a confident, neutral tone. Not tutorial voice, not first-person
  narration. Unresolved items go under "Follow-ups".
- **Roadmap status:** `docs/roadmap.md` is the single source of truth for progress. Update its
  Progress table when a phase starts or finishes, and tick Definition of done items only when they
  are actually complete.
- **Public repo:** written for an outside audience. Never commit secrets, personal information,
  or private notes. The gitignored `notes/` folder and `CLAUDE.local.md` are private: read them for
  context if present, but never commit or quote them in public docs.

## Every slice ends with
- Tests, `ruff` and `mypy` passing locally; CI passing on the PR.
- Docs updated as above, including the roadmap Progress table.
- A PR with a short summary of what was built and why, plus open questions from rule 2.

## Architecture principles
1. API layer is separate from execution logic.
2. Workflows are persistent state machines; invalid transitions are rejected.
3. PostgreSQL is the source of truth for workflow state. Redis, if used, is never the only copy.
4. Explicit task dependencies (a DAG); detect cycles.
5. Persist state transitions before reporting them to clients.
6. Design for at-least-once delivery with idempotent operations. Do not claim exactly-once.
7. Events are an observable, persisted record of execution (clients reconnect via event IDs).
8. Business logic is separate from infrastructure.
9. Modular monolith with independently run workers. No microservices.
10. Write the scheduler and executor ourselves; use provider SDKs underneath, not an orchestration framework.

## Stack and tooling
Python 3.12+, `uv`, FastAPI, Pydantic, SQLAlchemy 2.0 (async) with `asyncpg`, Alembic, PostgreSQL,
asyncio, pytest + HTTPX, `ruff`, `mypy`, Docker Compose, GitHub Actions. Frontend later: React,
TypeScript, Tailwind, React Flow. Rationale: `docs/technology-guide.md` and
`docs/decisions/0002-slice-1-tooling.md`.

## Conventions
- Type hints everywhere. `ruff` for lint and format, `mypy` for types.
- Tests run against a real PostgreSQL, not SQLite, because locking behaviour differs.
- Tests never call real LLM APIs. Use a fake provider behind the provider interface so tests are
  free, deterministic, and need no API keys in CI.
- Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, `refactor:`).
- Config via environment variables; keep `.env.example` current; never commit secrets.
- Structured logging; never log secrets, tokens or sensitive personal data.
- Cloud sessions start from a fresh clone, so anything needed to run tests must be committed
  or part of the environment setup script.

## Commands
First time: `cp .env.example .env`. Backend commands run from `backend/`.
- Start PostgreSQL: `docker compose up -d db` (host port 5433 by default)
- Install: `uv sync`
- Run: `uv run alembic upgrade head && uv run uvicorn app.main:app --reload` (OpenAPI docs at `/docs`)
- Test: `uv run pytest` (needs the database running; creates `agentfleet_test` on first run)
- Lint / format / type-check: `uv run ruff check . && uv run ruff format --check . && uv run mypy`
- Migrate: `uv run alembic upgrade head`; new migration: `uv run alembic revision --autogenerate -m "<message>"`
  (review the generated file by hand); drift check: `uv run alembic check`

## Security non-negotiables
- Never give an LLM-controlled agent an unrestricted shell, arbitrary Python execution, or
  unrestricted filesystem access.
- Tools are allowlisted per agent, with validated arguments, timeouts and output limits.
- Treat agent-generated arguments and external log/document content as untrusted input
  (prompt injection applies).
- Enforce authorization on the backend, including per-workspace data isolation.

## Scope guard
- P0: end-to-end incident workflow, persistent state, scheduling and dependencies, agent
  execution, basic retry/recovery, execution history, working frontend, tests, deployment.
- P1: concurrent workers, worker recovery, checkpoints, idempotency, human approval,
  tool permissions, traces, evaluation framework.
- P2: analytics, model comparisons, benchmarks, advanced editor.
- Do not start P2 while P0 is unfinished. Out of scope: agent marketplace, arbitrary user code
  execution, Kubernetes, multi-region, billing, custom models.

## Current status
See the Progress table in `docs/roadmap.md` and the latest file in `docs/slices/`.
