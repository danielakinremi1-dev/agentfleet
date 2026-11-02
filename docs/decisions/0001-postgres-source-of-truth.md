# ADR-0001: PostgreSQL as the workflow state store

Status: accepted

## Context
Workflow execution must survive restarts, worker crashes and retries, and every state
transition must be inspectable after the fact.

## Decision
Persist workflow, task, attempt, checkpoint, approval and event state in PostgreSQL.
Workers claim jobs from PostgreSQL using leases. Redis, if added later, is only for pub/sub or
caching and is never the only copy of execution state.

## Alternatives considered
- **Redis-only state:** fast, but state can be lost and is hard to query historically.
- **External workflow engine (for example Temporal):** powerful, but hides the mechanics this project
  is meant to demonstrate. Can be re-evaluated if complexity justifies it.

## Consequences
- Durable, queryable history and transactional consistency between state changes and events.
- More coordination logic to implement: claiming, leases, heartbeats, idempotency.
- Polling-based claiming needs benchmarking under load (Phase 8).
