# AgentFleet roadmap

The single source of truth for scope, order and progress.

- Why the plan has this shape: [ADR-0007](decisions/0007-roadmap-restructure.md)
- How work is delivered (branches, pull requests, checks, releases): [CONTRIBUTING.md](../CONTRIBUTING.md)
- How the system works today: [architecture overview](architecture/README.md)

## Where the project stands
_Rewritten at the end of every phase._

**Phase 0 is complete.** The repository contains a tested FastAPI service backed by PostgreSQL, with
versioned schema migrations and endpoints to create and read workflow templates. Every change reaches
`main` through a pull request that must pass lint, strict type checks, migration checks and a test
suite run against a real database. Workflows cannot be executed yet; that work starts in Phase 1.

## Progress

| Phase | Focus | Release | Status |
|---|---|---|---|
| 0 | Foundation | v0.1.0 | Done (license choice pending) |
| 1 | Workflow core: runs and state machines | v0.2.0 | Not started |
| 2 | Execution engine | v0.3.0 | Not started |
| 3 | Durable execution | v0.4.0 | Not started |
| 4 | Agents and tools | v0.5.0 | Not started |
| 5 | Security and human approval | v0.6.0 | Not started |
| 6 | Live observability and operator UI | v0.7.0 | Not started |
| 7 | Deployment and public demo | v0.8.0 | Not started |
| 8 | Evaluation | v0.9.0 | Not started |
| 9 | Performance | v0.10.0 | Not started |
| 10 | Presentation | v1.0.0 | Not started |

---

## What is being built

AgentFleet runs multi-step AI workflows reliably. A workflow is a graph of tasks; tasks are executed
by workers, survive crashes and restarts, are retried safely, and leave a complete record of what
happened. The first application is incident investigation: specialized agents gather evidence with
controlled tools, analyze it, challenge the diagnosis and produce an evidence-backed report, pausing
for human approval before any consequential action.

The engineering objective is the orchestration backend: durable execution, safe concurrency, failure
recovery, observability and security. Incident investigation is the use case that exercises it.

**Primary demonstration.** Submit an incident, watch agents run concurrently, see a worker crash and
the run recover without repeating finished work, approve a proposed remediation, read the report,
and inspect the full trace with cost and timing.

**Not in scope.** An agent marketplace, arbitrary user code execution, a general visual programming
language, Kubernetes, multiple regions, billing, custom models, autonomous production remediation.

## Priorities

| Priority | Meaning | Contents |
|---|---|---|
| **P0** | The project is incomplete without it | Workflow core, execution engine and durable execution, including concurrent workers, leases, retries and idempotent submission (Phases 1-3). Persisted execution history. The incident workflow end to end on the deterministic fake provider with allowlisted tools (Phase 4). Runs list and live run detail in the UI (Phase 6). Public deployment (Phase 7). Tests, including failure injection, and documentation throughout. |
| **P1** | Major differentiators | Authentication, workspaces and roles; human approval; audit log (Phase 5). A real LLM provider adapter. Traces and metrics. Evaluation harness (Phase 8). A focused benchmark report (Phase 9). |
| **P2** | Polish | Workflow builder UI, analytics page, model comparison reports, distributed tracing, scheduling beyond concurrency limits. |

P2 does not start while P0 is unfinished. A public deployment requires at least the authentication
and quota work from Phase 5.

**If time runs short, cut in this order:** Phase 9 to a single claim-throughput benchmark; Phase 8 to
three scenarios with no comparison report; Phase 6 to the run detail view only; Phase 5 to
single-workspace token authentication with approvals kept. Phases 1-3 are not cut.

## How the plan is delivered

| Unit | Size | Ends with |
|---|---|---|
| Phase | One capability of the system | End-of-phase review, changelog section, release tag |
| Slice | About 2-4 hours | One pull request and one slice note in [`slices/`](slices/) |
| Step | One checkbox below | One commit |

- **Every phase is bracketed by two summaries.** The start-of-phase summary states the objective, why it
  comes now, what can be demonstrated at the end and which concepts it introduces. The end-of-phase
  review records what was delivered, the evidence, the decisions taken, deviations from the plan and
  follow-ups. Phase 0 below is the worked example.
- **Detail is added one phase ahead.** The next two phases list their steps. Later phases list slices
  only; their steps are written when the phase starts, using what earlier phases taught.
- **Core subsystems are designed before they are built.** The first step of the relevant slice is a
  design doc in [`design-docs/`](design-docs/). Single decisions are recorded as ADRs in [`decisions/`](decisions/).
- **Each phase closes with the project presentable:** README status, demo commands and changelog are
  updated as part of the phase, not deferred to Phase 10.

**Presentation checkpoints.** Points at which the project stands on its own:

| Checkpoint | After | What can be shown |
|---|---|---|
| A | Phase 3 | A durable execution engine: crash-recovery demo from a fresh clone, the failure-injection suite, and the design docs behind it |
| B | Phase 7 | A public link where an investigation can be launched and watched live |
| C | Phase 10 | The complete project with evaluation results, a benchmark report and a video walkthrough |

The plan contains about 45 slices.

---

## Phase 0: Foundation (v0.1.0)

**Start-of-phase summary**
- **Objective:** a clean repository in which code can be written, checked and merged safely.
- **Why first:** every later phase depends on the database, the test setup and the delivery pipeline.
- **Demo at the end:** clone, `make setup && make up && make run`, create a workflow template through the API.
- **Concepts introduced:** async request handling, units of work and transactions, schema migrations,
  database constraints as guarantees, continuous integration.

**Slices**
- [x] **Backend scaffold** ([slice note](slices/01-backend-scaffold.md), PR #1): uv project, FastAPI app,
  async sessions, first migration, template endpoints, tests on PostgreSQL, CI.
- [x] **Delivery workflow** ([slice note](slices/02-delivery-workflow.md), PR #2): Makefile, coverage gate,
  protected `main`, PR template, changelog, Dependabot.
- [x] **Roadmap restructure** ([slice note](slices/03-roadmap-restructure.md), PR #3): this plan, the
  architecture overview and the design-doc process.
- [ ] **License** chosen and added (owner decision).

**Exit criteria**
- [x] The application starts locally with documented commands.
- [x] Tests run against PostgreSQL locally and in CI.
- [x] `main` cannot change without a passing pipeline.
- [x] The repository explains itself: README, roadmap, architecture overview, decisions.

**End-of-phase review**
- **Delivered:** a FastAPI service with typed configuration, a pooled async database layer, three tables
  (`workflow_templates`, `workflow_runs`, `tasks`) created by a reviewed migration, five endpoints, and a
  Makefile-driven pipeline enforced by branch protection.
- **Evidence:** 34 tests with 100% branch coverage of `app/`. They include five concurrent creates of one
  template name producing exactly one success, raw SQL failing against CHECK, UNIQUE and foreign-key
  constraints, a failed commit leaving no partial rows, and a migration downgrade and upgrade round trip.
- **Decisions:** PostgreSQL as source of truth ([ADR-0001](decisions/0001-postgres-source-of-truth.md)),
  tooling ([0002](decisions/0002-slice-1-tooling.md)), data model ([0003](decisions/0003-initial-data-model.md)),
  session and transaction boundaries ([0004](decisions/0004-session-and-transaction-boundaries.md)),
  test database strategy ([0005](decisions/0005-test-database-strategy.md)),
  delivery workflow ([0006](decisions/0006-delivery-workflow.md)), roadmap structure ([0007](decisions/0007-roadmap-restructure.md)).
- **Deviations:** the original plan placed run and task tables in a later phase; they were created here so
  the constraint tests could cover them. User and Agent CRUD were dropped from the early plan (ADR-0007).
- **Carried forward:** structured logging and request IDs, keyset pagination (Phase 1); UUIDv7 keys;
  a single source for the application version.

---

## Phase 1: Workflow core, runs and state machines (v0.2.0)

**Start-of-phase summary**
- **Objective:** a template can be instantiated as a run whose tasks and dependencies are database rows,
  and the lifecycle rules of runs and tasks are enforced.
- **Why now:** everything the engine does later is a state transition on these rows. If transitions can be
  invalid or raced, no amount of retry logic on top makes execution reliable.
- **Demo at the end:** create a run through the API and read back its task graph; a cyclic template is
  rejected with the cycle named; an invalid transition is refused.
- **Concepts introduced:** directed acyclic graphs and topological ordering, finite state machines,
  compare-and-set updates, uniform API errors, structured logging.

**Slices**
- [ ] **Dependency graph validation**
  - [ ] Design doc 0001: run lifecycle (run creation, task materialization, run and task state machines)
  - [ ] `app/orchestration/dag.py`: cycle detection (Kahn's algorithm) returning a topological order or the tasks on a cycle; unit tests for chain, diamond, two-node cycle, long cycle and disconnected graphs
  - [ ] Template validation rejects cyclic definitions with a 422 that names the cycle
- [ ] **Run creation**
  - [ ] Migration `0002`: `task_dependencies` (composite primary key, cascading foreign keys, no self-reference)
  - [ ] `create_run` service: the run, one task per definition entry and the dependency rows are inserted in one transaction
  - [ ] `POST /api/workflows/{id}/runs`, `GET /api/runs/{id}` (run with tasks and dependencies), `GET /api/runs`
  - [ ] Tests: the materialized graph matches the definition; a failure part-way leaves no rows; unknown template is 404
- [ ] **State machines**
  - [ ] Allowed transitions for runs and tasks declared as data, in one module
  - [ ] Transition functions use compare-and-set (`UPDATE ... WHERE id = ? AND status = ?`), so a stale or concurrent transition changes no row and raises a domain error
  - [ ] Tests: every (from, to) pair, exhaustively; two sessions racing one transition produce exactly one winner
  - [ ] ADR: transitions enforced in the application with compare-and-set, versus database triggers
- [ ] **API consistency and logging**
  - [ ] One error format for every failure (RFC 9457 problem details) with stable error codes, mapped in one place
  - [ ] Request ID middleware: accepted from `X-Request-ID` or generated, returned in responses, bound into logs
  - [ ] Structured JSON logging with a redaction rule for sensitive fields
  - [ ] Keyset pagination on list endpoints, replacing offset pagination

**Exit criteria**
- [ ] A run created from a template can be read back with its tasks and dependencies.
- [ ] No cyclic template can be stored.
- [ ] Every invalid state transition is rejected, and the transition table is tested exhaustively.
- [ ] All error responses share one documented format, and every log line carries a request ID.

**End-of-phase review:** _written when the phase closes._

---

## Phase 2: Execution engine (v0.3.0)

**Start-of-phase summary**
- **Objective:** runs execute outside the request cycle, in dependency order, on independently run
  worker processes, and every state change is recorded as an event.
- **Why now:** the state machine exists; this phase drives it. Mock task handlers are used so the engine is
  proven before any AI is involved.
- **Demo at the end:** `make demo` submits the incident template with mock handlers, two workers process
  independent tasks in parallel, and the event history is printed.
- **Concepts introduced:** a job queue in PostgreSQL, row locks and `FOR UPDATE SKIP LOCKED`, scheduling by
  dependency readiness, an executor interface, transactional event recording, graceful shutdown.

**Slices**
- [ ] **Task handlers and executor interface**
  - [ ] Design doc 0002: scheduling and job claiming
  - [ ] Template task definitions gain a `handler` name and a `config` object, validated against a registry
  - [ ] `Executor` protocol (`execute(TaskContext) -> TaskResult`) and mock handlers (`noop`, `sleep`, `fail_n_times`)
- [ ] **Scheduler**
  - [ ] Readiness as one query: pending tasks whose dependencies are all completed become `queued`
  - [ ] Run lifecycle: first queued task starts the run; all tasks completed completes it; a permanent task failure fails it and blocks dependents
  - [ ] Tests: chain, diamond and fan-out graphs; a dependent task is never queued early
- [ ] **Worker**
  - [ ] `python -m app.workers`: poll, claim queued tasks with `SELECT ... FOR UPDATE SKIP LOCKED`, execute, persist result and transition together
  - [ ] Concurrency limit, per-task timeout, graceful shutdown on SIGTERM (stop claiming, finish in-flight tasks)
  - [ ] Tests on real concurrent connections: two workers never execute the same task; independent tasks overlap in time; a timeout fails the task
- [ ] **Execution events**
  - [ ] Migration: `execution_events` (monotonic ID, run, task, type, JSONB payload)
  - [ ] Each state transition writes its event in the same transaction
  - [ ] `GET /api/runs/{id}/events?after=<id>`
  - [ ] Test: a failure between transition and event leaves neither
- [ ] **Containers and demo**
  - [ ] One image with API and worker entry points, non-root user; Compose services `api` and `worker`; image build in CI
  - [ ] `make demo`: seed the template, start a run, print the event history

**Exit criteria**
- [ ] A submitted run returns its ID immediately and completes in the background (scenario 1).
- [ ] Independent tasks execute concurrently; dependent tasks wait (scenarios 2 and 3).
- [ ] Two workers on one queue never execute the same task.
- [ ] The full history of a run can be reconstructed from its events.

**End-of-phase review:** _written when the phase closes._

---

## Phase 3: Durable execution (v0.4.0)

**Start-of-phase summary**
- **Objective:** a run survives worker crashes, restarts, timeouts and duplicate delivery without losing
  work or applying it twice.
- **Why now:** this is the property that separates an orchestration engine from a task loop, and it is far
  easier to build before real agents and external calls are attached.
- **Demo at the end:** `make demo-crash` kills a worker with SIGKILL in the middle of a task; another worker
  takes the task over after its lease expires; the run completes and no finished task is repeated.
- **Concepts introduced:** leases and heartbeats, fencing tokens, at-least-once delivery, idempotency keys,
  exponential backoff with jitter, retryable and permanent errors, cooperative cancellation.

**Slices** (steps are written when the phase starts)
- [ ] **Attempts and failure model.** Design doc 0003: what can fail between any two steps and what the
  system guarantees in each case. `task_attempts` records every attempt's worker, timing and outcome.
- [ ] **Leases and heartbeats.** A claim carries an owner and an expiry; workers extend it while working; a
  reaper returns expired tasks to the queue; a fencing token stops a worker that lost its lease from
  recording a result. Failure injection: crash mid-task, lease expiry, late result from a stale worker.
- [ ] **Retry policy.** Per-task maximum attempts; exponential backoff with jitter; retryable versus
  permanent errors; exhaustion fails the task and the run.
- [ ] **Idempotency.** `Idempotency-Key` on run creation returns the original run for a repeated request.
  Each attempt exposes a stable key for handlers to pass to external systems. Duplicate-delivery test.
- [ ] **Cancellation.** Cancel endpoint; waiting tasks are cancelled immediately, running tasks
  cooperatively; documented behaviour for side effects that already happened.
- [ ] **Recovery demo and failure suite.** API and workers restart mid-run without repeating completed
  tasks; `make demo-crash`; the failure-injection suite runs in CI.

**Exit criteria**
- [ ] A task whose worker dies is completed by another worker (scenario 7).
- [ ] Restarting every process mid-run loses no completed work (scenario 8).
- [ ] A task delivered twice produces one result and one side effect (scenario 9).
- [ ] A failing task retries with backoff and then succeeds or fails permanently (scenario 6).

**End-of-phase review:** _written when the phase closes._ This phase is presentation checkpoint A.

---

## Phase 4: Agents and tools (v0.5.0)

**Start-of-phase summary**
- **Objective:** task handlers become LLM agents that use controlled tools, and the incident
  investigation workflow runs end to end.
- **Why now:** the engine already handles failure, so provider errors, invalid outputs and tool timeouts
  become ordinary retryable or permanent errors instead of special cases.
- **Demo at the end:** submit an incident; four agents run on the deterministic fake provider and produce a
  report whose claims cite evidence. With an API key, the same run uses a real model.
- **Concepts introduced:** provider abstraction, structured output validation, tool allowlists and
  sandboxing, untrusted input and prompt injection, cost accounting, evidence provenance.

**Slices** (steps are written when the phase starts)
- [ ] **Provider interface and fake provider.** Design doc 0004: agent execution and the tool sandbox. A
  provider protocol, a scripted deterministic fake, and usage (tokens, latency, cost) recorded per call.
- [ ] **Structured outputs.** A Pydantic schema per agent; invalid output gets one repair attempt, then a
  permanent failure.
- [ ] **Tool registry and sandbox.** Tools declare an input schema, a timeout and an output limit; agents
  have allowlists; every call is recorded. Simulated tools (log search, deployment history, metrics,
  service health) read a synthetic incident dataset.
- [ ] **Agent executor.** The agent loop as an `Executor`; tool calls completed in an earlier attempt are
  reused after a retry.
- [ ] **Incident investigation workflow.** Scout, analysis, verification and report agents; a seeded
  template; report claims reference evidence IDs; verification flags unsupported claims.
- [ ] **Real provider adapter.** One provider SDK behind the interface, enabled by an environment key; rate
  limits and timeouts mapped to retryable errors. Never used in CI.

**Exit criteria**
- [ ] An invalid structured response and a tool timeout are both handled by the engine (scenarios 4 and 5).
- [ ] A completed run produces a report with traceable evidence (scenario 12).
- [ ] No agent can call a tool outside its allowlist or with unvalidated arguments.
- [ ] The whole test suite runs with no API key.

**End-of-phase review:** _written when the phase closes._

---

## Phase 5: Security and human approval (v0.6.0)

**Start-of-phase summary**
- **Objective:** users authenticate, see only their workspace's data, act within their role, and approve
  consequential actions before they run.
- **Why now:** it must precede any public deployment, and it adds ownership columns to tables that already
  hold data, which is the realistic way such a change arrives.
- **Demo at the end:** a user from another workspace receives 404 for a run that exists; an agent proposes
  a remediation, the run pauses, an operator approves it and the run resumes.
- **Concepts introduced:** authentication and authorization, tenant isolation, expand and contract
  migrations, pause and resume in a state machine, audit logging, threat modelling.

**Slices** (steps are written when the phase starts)
- [ ] **Authentication.** Design doc 0005 with a threat model. Users, password hashing, expiring access
  tokens; every `/api` endpoint protected.
- [ ] **Workspaces and roles.** `workspace_id` added to existing tables with an expand, backfill and
  contract migration; admin, operator and viewer roles enforced in services; cross-workspace access tests.
- [ ] **Human approval.** Approval-required tools pause their task; approval records carry requester,
  decision, reason and expiry; approve and reject endpoints; the run resumes with its context intact.
- [ ] **Audit log and hardening.** Append-only audit records; rate limiting on authentication; CORS; secret
  redaction in logs and traces; prompt-injection tests on tool arguments and log content; dependency
  scanning in CI; `SECURITY.md` and a security checklist.

**Exit criteria**
- [ ] A run pauses for approval and resumes after a decision (scenario 10).
- [ ] A user cannot read or change another workspace's data (scenario 11).
- [ ] Every security-relevant action has an audit record.
- [ ] The security checklist is complete.

**End-of-phase review:** _written when the phase closes._

---

## Phase 6: Live observability and operator UI (v0.7.0)

**Start-of-phase summary**
- **Objective:** a person can watch a run as it happens and inspect everything about it afterwards.
- **Why now:** the events, attempts and tool records already exist; this phase exposes them.
- **Demo at the end:** open a run in the browser, watch the task graph update live, drop the connection,
  reconnect and see nothing missed.
- **Concepts introduced:** server-sent events and resumable streams, metrics and traces, a typed frontend
  consuming a typed API.

**Slices** (steps are written when the phase starts)
- [ ] **Live event stream.** Design doc 0006: event delivery. A streaming endpoint replays from
  `Last-Event-ID` out of the persisted events and then follows live. Reconnect test.
- [ ] **Traces and metrics.** One API call returns a run's trace (attempts, tool calls, tokens, cost).
  A Prometheus endpoint exposes queue depth, claim latency, task duration and retries.
- [ ] **UI scaffold and runs.** React, TypeScript and Tailwind; sign in; runs list; submit an incident.
- [ ] **Run detail.** Live task graph (React Flow), timeline, and an inspector for inputs, outputs, tool
  calls, retries and cost.
- [ ] **Approvals.** Pending approvals with their evidence; approve and reject.

The workflow builder and analytics pages are P2. Visual direction: [`ui-design/`](ui-design/README.md).

**Exit criteria**
- [ ] A run can be launched and watched live from the browser.
- [ ] A client that reconnects receives every event it missed, in order.
- [ ] Every task's inputs, outputs, tool calls, retries and cost can be inspected.

**End-of-phase review:** _written when the phase closes._

---

## Phase 7: Deployment and public demo (v0.8.0)

**Start-of-phase summary**
- **Objective:** the application runs on the public internet and can be explored without installing anything.
- **Why now:** it is placed before evaluation and performance work so that a working link exists as early as
  the product is safe to expose.
- **Demo at the end:** open the public URL, launch a sample investigation and inspect the result.
- **Concepts introduced:** production container images, environment-specific configuration, migrations
  during deploys, backups, health checks, operating a service.

**Slices** (steps are written when the phase starts)
- [ ] **Production images and configuration.** Hardened images for API, worker and frontend; full-stack
  Compose; per-environment settings; a documented migration procedure for deploys.
- [ ] **Deployment.** Hosting decision recorded as an ADR (paid services need owner approval); HTTPS;
  managed PostgreSQL with backups; health checks; error reporting; deploy on release tag.
- [ ] **Public demo mode and runbook.** A seeded demo workspace with synthetic data, the fake provider by
  default, execution quotas and restricted tools. A runbook for deploy, rollback, backup and restore.

**Exit criteria**
- [ ] A visitor can launch an investigation, watch it and inspect a completed run from a public link.
- [ ] A deploy is one tagged release, and a rollback is documented and rehearsed.
- [ ] The demo cannot be used to spend money or reach anything outside its sandbox.

**End-of-phase review:** _written when the phase closes._ This phase is presentation checkpoint B.

---

## Phase 8: Evaluation (v0.9.0)

**Start-of-phase summary**
- **Objective:** measure whether the agents reach the correct diagnosis, and detect when a change makes them worse.
- **Why now:** it needs the complete incident workflow and benefits from the trace data added in Phase 6.
- **Demo at the end:** run the scenario suite and read a report of correctness, evidence coverage, time and cost.
- **Concepts introduced:** ground-truth datasets, deterministic versus model-based grading, regression testing for AI behaviour.

**Slices** (steps are written when the phase starts)
- [ ] **Scenario dataset.** Six simulated incidents, each with a ground-truth cause, supporting evidence,
  expected diagnosis and recommendations.
- [ ] **Evaluation runner.** Runs scenarios repeatedly and records diagnosis correctness, evidence
  coverage, unsupported claims, completion rate, duration, tokens and cost. Deterministic assertions first.
- [ ] **Comparison and regression.** A report comparing prompt or model versions; the suite runs in CI on
  the fake provider to catch regressions in orchestration and output parsing.

**Exit criteria**
- [ ] The same scenario can be replayed and scored reproducibly.
- [ ] A change to prompts, tools or workflow shape produces a before and after comparison.

**End-of-phase review:** _written when the phase closes._

---

## Phase 9: Performance (v0.10.0)

**Start-of-phase summary**
- **Objective:** know, with numbers, how the engine behaves under load and where it stops scaling.
- **Why now:** measuring earlier would measure code that was still changing.
- **Demo at the end:** a published report: throughput against worker count, latency percentiles, the
  bottlenecks found and what was changed.
- **Concepts introduced:** load generation, latency percentiles, query plans, indexing for queue workloads,
  connection pool sizing, backpressure and limits.

**Slices** (steps are written when the phase starts)
- [ ] **Benchmark harness.** A load generator and measurements of run-creation latency, claim latency,
  scheduling latency and tasks per second against worker count. Methodology and hardware recorded.
- [ ] **Evidence-based optimization.** Query plans for the claim and readiness queries; a partial index on
  claimable tasks; pool sizing; polling versus `LISTEN/NOTIFY`. Before and after numbers.
- [ ] **Limits and overload.** Per-workspace concurrency limits, API rate limits and provider budgets;
  behaviour under worker overload, a slow database and provider rate limiting; the performance report.

**Exit criteria**
- [ ] Benchmarks are reproducible from one documented command.
- [ ] Each optimization is justified by a measurement.
- [ ] Known limits and the first bottleneck at higher scale are stated.

**End-of-phase review:** _written when the phase closes._

---

## Phase 10: Presentation (v1.0.0)

**Start-of-phase summary**
- **Objective:** a reviewer can understand what the project does, how it works and why it was built this
  way in a few minutes.
- **Why last:** each phase already keeps the README and docs current; this phase consolidates them.
- **Demo at the end:** the README, a short video and the public link tell the whole story.

**Slices**
- [ ] **README and architecture documentation.** Final README with screenshots, diagram, demo link, test
  instructions and known limitations; subsystem pages consolidated from the design docs.
- [ ] **Demo video.** A 2-4 minute walkthrough that includes a failure and its recovery.
- [ ] **Final review.** The definition of done verified item by item; `v1.0.0` released.

**End-of-phase review:** _written when the phase closes._ This phase is presentation checkpoint C.

---

## Requirements that span phases

### Production practices and where they enter

| Practice | Phase |
|---|---|
| Typed configuration from the environment; no secrets in the repository | 0 (done) |
| Versioned, reversible migrations with a drift check | 0 (done) |
| Protected `main`, required CI, coverage gate, dependency update PRs | 0 (done) |
| Uniform error format, request IDs, structured logs | 1 |
| Compare-and-set state transitions | 1 |
| Keyset pagination | 1 |
| Queue claiming with row locks | 2 |
| State changes and their events committed together | 2 |
| Graceful shutdown; container images built in CI | 2 |
| Leases, heartbeats and fencing tokens | 3 |
| Retries with backoff and jitter; idempotency keys | 3 |
| Timeouts and output limits on every external call | 4 |
| Authentication, authorization, tenant isolation, audit log | 5 |
| Schema changes on populated tables (expand, backfill, contract) | 5 |
| Dependency vulnerability scanning | 5 |
| Metrics and traces | 6 |
| Health checks, backups, runbook, deploy on tag | 7 |
| Quotas and rate limits | 5, 7, 9 |
| Load testing with published numbers | 9 |

### Testing layers

| Layer | Verifies | From |
|---|---|---|
| Unit | Pure logic: validation, graph algorithms, transition tables, backoff | Phase 0 |
| Integration | API, services and database together on PostgreSQL | Phase 0 |
| Concurrency | Racing connections: claims, transitions, duplicate submissions | Phase 0 |
| Failure injection | Crash mid-task, lease expiry, duplicate delivery, restart | Phase 3 |
| Security | Authorization, isolation, input validation, prompt injection | Phase 4 |
| End to end | The scenarios below, through the public API | Phase 2 |
| Evaluation | Agent correctness against ground truth | Phase 8 |
| Performance | Throughput and latency under load | Phase 9 |

Tests never call a real LLM API. Tests run against PostgreSQL, not SQLite.

### Essential end-to-end scenarios

| # | Scenario | Phase |
|---|---|---|
| 1 | A user submits a workflow and receives a run ID immediately | 2 |
| 2 | Multiple independent tasks execute concurrently | 2 |
| 3 | A dependent task waits until its prerequisites complete | 2 |
| 4 | An agent returns an invalid structured response | 4 |
| 5 | A tool call times out | 4 |
| 6 | A task fails and successfully retries | 3 |
| 7 | A worker crashes during execution | 3 |
| 8 | The application restarts and recovers the workflow | 3 |
| 9 | A duplicate task delivery does not cause duplicate side effects | 3 |
| 10 | A workflow pauses for human approval | 5 |
| 11 | An unauthorized user attempts to access another user's workflow | 5 |
| 12 | A workflow completes and produces a report with traceable evidence | 4 |

### Security by stage

| Stage | Requirement |
|---|---|
| Foundation | Secrets and configuration outside the repository; pinned dependencies |
| API | Request validation, parameterized queries, size limits, no internal details in errors |
| Orchestration | Timeouts, concurrency limits, transitions that cannot be bypassed |
| Agents | Tool allowlists, validated arguments, output limits, prompt-injection defences |
| Multi-user | Authentication, authorization on the backend, workspace isolation |
| Approval | Authorization of approvers, audit history, safe execution of approved actions |
| Deployment | HTTPS, secret management, backups, monitoring |
| Public demo | Synthetic data, quotas, restricted tools, abuse protection |

An LLM-controlled agent is never given an unrestricted shell, arbitrary code execution or unrestricted
filesystem access.

---

## Definition of done

The project is ready to present when every item is true. Items are ticked only when complete.

**Core product**
- [ ] A user can submit an incident investigation.
- [ ] The workflow is created and persisted.
- [ ] Multiple specialized agents execute tasks.
- [ ] Task dependencies are respected.
- [ ] Independent tasks execute concurrently.
- [ ] The final report includes evidence and recommendations.

**Backend engineering**
- [ ] Clean modular architecture.
- [x] Database migrations.
- [ ] Background workers.
- [ ] Durable workflow state.
- [ ] Retry and timeout handling.
- [ ] Checkpointing and recovery.
- [ ] Idempotent task handling.
- [ ] Cancellation support.

**AI engineering**
- [ ] Structured agent outputs.
- [ ] Controlled tool execution.
- [ ] Provider abstraction.
- [ ] Evidence provenance.
- [ ] Human approval.
- [ ] Evaluation scenarios.
- [ ] Cost and latency tracking.

**Security and reliability**
- [ ] Authentication.
- [ ] Authorization.
- [ ] User data isolation.
- [ ] Tool permission restrictions.
- [ ] Audit history.
- [ ] Input validation.
- [ ] Security testing.
- [ ] Failure recovery tests.

**Product and deployment**
- [ ] Interactive dashboard.
- [ ] Live execution updates.
- [ ] Workflow visualization.
- [ ] Execution inspector.
- [ ] Dockerized application.
- [x] Automated CI.
- [ ] Public deployment.
- [ ] Demo workflow.
- [ ] Documentation.
- [ ] Video walkthrough.

## What the finished project must be able to explain
1. How the problem was identified and turned into requirements.
2. How the database and application architecture were designed.
3. How asynchronous processing and concurrency work.
4. How failure recovery works, and what is and is not guaranteed.
5. How agents and tools are integrated and constrained.
6. How execution is made secure and observable.
7. How the system is tested under normal and abnormal conditions.
8. How it is deployed and operated.
9. What would change to support substantially more load.

## Plan history
- **2026-11:** restructured from the original eleven-phase plan. Phases were reordered, the early phases
  were given step checklists, and scope priorities were revised. See [ADR-0007](decisions/0007-roadmap-restructure.md).
