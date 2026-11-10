# ADR-0007: Roadmap restructure and scope priorities

Status: accepted

## Context
The original roadmap described eleven phases in about 1,500 lines. After the first slice, a review
found problems with its shape for a project whose engineering objective is the orchestration backend:

1. **No public deployment until Phase 9 of 10**, so the project could not be shown running for most of its life.
2. **The backend differentiators were second priority.** Concurrent workers, worker recovery, checkpoints
   and idempotency were P1, while a six-page frontend was P0.
3. **Speculative work came early.** Phase 1 called for User and Agent CRUD endpoints before any feature
   needed users or agents.
4. **Events were tied to the frontend** (Phase 6), although persisting state changes with their events is
   an engine concern that later phases depend on.
5. **Performance benchmarks were P2**, although measured numbers are among the most concrete evidence a
   backend project can offer.
6. **Phases had no checklists, entry summaries or exit criteria**, so progress and completion were judgements.

## Decision
1. **Order by backend risk.** Workflow core, execution engine and durable execution (Phases 1-3) come
   first and use mock task handlers. Agents (Phase 4) are built on an engine that already handles failure.
2. **Promote durability to P0.** Concurrent workers, leases, retries with backoff and idempotent
   submission are part of the minimum project. Phases 1-3 are never cut.
3. **Entities are created when a feature needs them.** Agent definitions arrive with agents (Phase 4),
   users with authentication (Phase 5). Phase 1 covers runs, dependencies and state machines only.
4. **Split events from the UI.** Events are persisted in the same transaction as each state transition
   from Phase 2. Streaming them to clients remains in Phase 6.
5. **Deploy before evaluation and performance work.** Deployment moves from Phase 9 to Phase 7. Evaluation
   becomes Phase 8 and performance Phase 9. Container images are introduced in Phase 2, so deployment is
   mostly configuration by the time it arrives.
6. **Reduce the frontend to three views** (runs list, live run detail with inspector, approvals). The
   workflow builder and analytics pages become P2.
7. **Promote a focused benchmark report to P1.** Broader analytics and model comparisons stay P2.
8. **The deterministic fake provider is sufficient for P0.** A real provider adapter is P1, so the
   project can be run, tested and demonstrated at no cost and with no API key.
9. **Give every phase a fixed structure:** a start-of-phase summary, slices as checkboxes, exit criteria
   and an end-of-phase review. Steps are detailed for the next two phases only, since later detail would
   be rewritten anyway.
10. **Each phase is a release** (`v0.1.0` to `v1.0.0`) and leaves the project presentable; three
    presentation checkpoints are named (after Phases 3, 7 and 10).
11. **Core subsystems get a design doc before implementation** ([`../design-docs/`](../design-docs/)).

Phase numbers changed for deployment (9 to 7), evaluation (7 to 8) and performance (8 to 9). References
in earlier documents and code comments were updated to the new numbers.

## Alternatives considered
- **Keep the original order.** Familiar, but leaves durability optional and the project unshown until the end.
- **Agents first.** Produces an impressive demo early, but on an engine that cannot yet survive a failure,
  and the hard backend work competes with prompt iteration for attention.
- **Deploy after Phase 3.** Earliest possible link, but with no UI and no authentication there is nothing
  safe or legible to expose; the Phase 3 checkpoint is a demo run from a clone instead.
- **Plan every phase to step level now.** Looks thorough, but detail written months ahead is wrong by the
  time it is used.

## Consequences
- The project is a credible backend system from Phase 3, before any AI feature exists.
- Authentication arrives after the core tables hold data, which requires an expand, backfill and contract
  migration. This is accepted, and treated as a deliberate exercise in changing a populated schema.
- The incident workflow, the most visible feature, arrives later than in an agents-first plan.
- The roadmap is shorter and must be extended at the start of each phase; that update is part of the
  phase's first slice.
