# Design docs

A design doc describes how a subsystem will work before it is built. It is written as the first step
of the slice that starts the subsystem and reviewed in that slice's pull request.

## Design doc or ADR?

| | Design doc | ADR ([`../decisions/`](../decisions/)) |
|---|---|---|
| Scope | A whole subsystem and how its parts interact | One decision |
| Written | Before building | When the decision is made |
| Answers | How will this work, and how can it fail? | What was chosen, over what, and why? |
| Changes | Updated while the subsystem is built; marked `implemented` when done | Immutable once accepted; superseded by a new ADR |

A design doc usually produces one or more ADRs for the decisions it settles.

## When one is required
Core subsystems, where a mistake in the design is expensive to fix later: state machines, scheduling
and job claiming, leases and retries, idempotency, agent execution and the tool sandbox,
authentication and authorization, event delivery. Routine endpoints and refactors do not need one.

## Index

| # | Subsystem | Phase | Status |
|---|---|---|---|
| 0001 | Run lifecycle: run creation, task materialization, run and task state machines | 1 | Planned |
| 0002 | Scheduling and job claiming | 2 | Planned |
| 0003 | Leases, retries and idempotency (failure model) | 3 | Planned |
| 0004 | Agent execution and the tool sandbox | 4 | Planned |
| 0005 | Authentication, authorization and threat model | 5 | Planned |
| 0006 | Event delivery and resumable streams | 6 | Planned |

Files are named `NNNN-short-name.md`.

## Template

```markdown
# Design NNNN: <subsystem>

Status: draft | accepted | implemented
Phase: <n>    Related ADRs: <links>

## Problem
What must this subsystem do, and what goes wrong without it?

## Goals and non-goals
What it guarantees. What it deliberately does not attempt.

## Design
Data model changes, components, and the main flows. Diagrams where they help.

## Failure modes
For each step: what if the process dies here, the database is unreachable, or the same
request arrives twice? State what the system guarantees in each case.

## Alternatives considered
Other designs and why they were not chosen.

## Test plan
The tests that will prove the guarantees, including failure-injection tests.

## Rollout
Migrations, ordering of changes, and anything that must be backfilled.

## Open questions
```
