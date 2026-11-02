# AgentFleet — Complete Project Roadmap

**Project type:** Backend-heavy AI application / developer tooling  
**Primary language:** Python  
**Primary goal:** Demonstrate professional backend engineering, independent problem-solving, AI agent orchestration, and end-to-end product development.  
**Secondary goal:** Deliver a visually distinctive, interactive application that is compelling to explore and demonstrate.

> **Project decision:** AgentFleet starts from a clean repository (no starter template).

## Progress

| Phase | Focus | Status |
|---|---|---|
| 0 | Repository and project foundation | Not started |
| 1 | Database and core backend | Not started |
| 2 | Workflow orchestration engine | Not started |
| 3 | Durable execution and failure recovery | Not started |
| 4 | AI agents and tool execution | Not started |
| 5 | Human approval and security | Not started |
| 6 | Observability and real-time frontend | Not started |
| 7 | Evaluation and quality measurement | Not started |
| 8 | Performance and scalability | Not started |
| 9 | Docker, CI/CD and deployment | Not started |
| 10 | Portfolio presentation | Not started |

---

# 1. Product vision and requirements

## 1.1 What problem does AgentFleet solve?

AI agents can perform useful tasks, but running them reliably in real applications introduces several problems:

- Workflows can take minutes or hours to complete.
- Individual agents can fail or return invalid results.
- Tasks may depend on the output of previous tasks.
- Multiple independent tasks should execute concurrently.
- Application restarts shouldn't destroy workflow progress.
- Tool access must be controlled and auditable.
- Developers need to understand why an agent made a particular decision.
- AI output quality, execution time, and API costs need to be measured.

AgentFleet addresses these problems through a centralized orchestration and observability platform.

## 1.2 Core user journey

The primary demonstration should follow this sequence:

1. A user opens AgentFleet and views the operations dashboard.
2. They select a workflow template: *Incident Investigation*.
3. They submit an incident description.
4. AgentFleet creates a workflow execution and assigns tasks.
5. Multiple agents begin investigating the incident.
6. The dashboard updates in real time as agents execute.
7. An agent encounters an issue, triggering a retry or recovery mechanism.
8. An agent proposes a remediation that requires human approval.
9. The user reviews the evidence and approves or rejects the action.
10. The workflow completes and produces a structured investigation report.
11. The user can inspect the complete execution history, agent activity, costs, and performance.

This should be the primary end-to-end experience that everything else supports.

## 1.3 Product capabilities

| Capability | Purpose |
|---|---|
| Workflow orchestration | Coordinate multi-step agent tasks |
| Durable execution | Preserve workflow progress across restarts |
| Concurrency | Execute independent tasks simultaneously |
| Failure recovery | Retries, timeouts, checkpoints and resumption |
| Observability | Inspect every execution step |
| Human approval | Control sensitive or consequential operations |
| Agent management | Define agent roles, models and permissions |
| Evaluation | Measure output quality and performance |
| Security | Authenticate users and enforce access controls |
| Performance monitoring | Measure latency, throughput and cost |

## 1.4 What AgentFleet is NOT

Avoid turning this into an excessively broad platform.

The first version does not need:

- A marketplace for agents.
- Arbitrary user-written code execution.
- A fully general visual programming language.
- Multiple deployment regions.
- Kubernetes.
- A complicated billing system.
- Hundreds of integrations.
- A custom AI model.
- A fully autonomous production remediation system.

These are potential future extensions, not requirements for a successful capstone.

---

# 2. Recommended technology stack

The stack should demonstrate transferable backend skills rather than simply use as many technologies as possible.

## Backend

| Technology | Purpose |
|---|---|
| Python | Primary programming language |
| FastAPI | HTTP API and application layer |
| Pydantic | Validation and structured schemas |
| SQLAlchemy | Database interaction and ORM |
| Alembic | Database migrations |
| PostgreSQL | Persistent application and workflow state |
| asyncio | Asynchronous execution and concurrency |
| WebSockets or SSE | Real-time execution updates |
| pytest | Automated testing |
| HTTPX | API and integration testing |

## AI and agent layer

| Technology | Purpose |
|---|---|
| LLM provider API | Agent reasoning and generation |
| Provider abstraction | Allow switching between models |
| Structured outputs | Consistent agent responses |
| Tool/function calling | Controlled access to external capabilities |
| Custom orchestration layer | Agent coordination and execution |

Use an established provider SDK or a lightweight agent framework where appropriate, but own the execution lifecycle: the orchestration logic is implemented in this project rather than delegated to a framework.

Do not make the entire project dependent on a single agent framework.

## Infrastructure

| Technology | Purpose |
|---|---|
| Docker | Application containerization |
| Docker Compose | Local development environment |
| Redis (optional initially) | Pub/sub, caching, coordination |
| GitHub Actions | CI and automated checks |
| Cloud hosting | Public deployment |
| Structured logging | Operational visibility |

**Important architectural decision:** PostgreSQL should be the source of truth for workflow state. Redis should not be the only place where execution information exists.

For the first implementation, a PostgreSQL-backed worker with durable jobs, leases, and checkpoints is a reasonable first implementation. A dedicated workflow engine such as Temporal can be evaluated later if the complexity justifies it.

## Frontend

Recommended:

- React
- TypeScript
- Tailwind CSS
- React Flow for workflow visualization
- A charting library for performance metrics

The backend is the main engineering focus, but the frontend should feel like a complete product.

---

# 3. High-level system architecture

The system should be separated into distinct responsibilities.

```text
                    AGENTFLEET
                         |
             ┌───────────▼───────────┐
             │      Frontend         │
             │  Dashboard / Workflow │
             └───────────┬───────────┘
                         |
                  HTTP / WebSocket
                         |
             ┌───────────▼───────────┐
             │      FastAPI          │
             │    API Layer          │
             └───────────┬───────────┘
                         |
             ┌───────────▼───────────┐
             │   Application Layer   │
             │ Workflow Management   │
             │ Authentication        │
             │ Approval Management   │
             └───────────┬───────────┘
                         |
             ┌───────────▼───────────┐
             │  Orchestration Engine │
             │                       │
             │ Dependency Management│
             │ Scheduling            │
             │ Execution State       │
             │ Retry / Recovery      │
             └───────────┬───────────┘
                         |
              ┌──────────┴──────────┐
              |                     |
      ┌───────▼────────┐    ┌──────▼────────┐
      │ Worker Pool    │    │ Event System  │
      │                │    │               │
      │ Agent Executor │    │ Execution Logs│
      │ Tool Executor  │    │ Event Stream  │
      └───────┬────────┘    └──────┬────────┘
              |                    |
       ┌──────▼────────────────────▼─────┐
       │           PostgreSQL            │
       │                                 │
       │ Workflows / Tasks / Agents      │
       │ Events / Checkpoints / Approvals│
       │ Results / Audit Records         │
       └─────────────────────────────────┘
```

### Architectural principles

1. Keep the API layer separate from execution logic.
2. Treat workflows as persistent state machines.
3. Keep individual agent execution independent of the orchestration engine.
4. Use explicit task dependencies.
5. Persist state transitions before reporting them to clients.
6. Make external actions idempotent wherever possible.
7. Treat events as an observable record of execution.
8. Keep business logic separate from infrastructure implementation.

Avoid starting with microservices. Build a modular monolith with independently managed workers. This provides architectural separation without unnecessary deployment complexity.

---

# 4. Detailed development roadmap

The following phases are ordered deliberately. Each phase should produce a working result before the next begins.

# PHASE 0 — Repository and project foundation

**Objective:** Establish a clean, maintainable development environment.

### Step 0.1 — Set up the repository

- Initialize a clean repository.
- Add a license, README and `.gitignore`.
- Establish a clean Git history from the first commit.

### Step 0.2 — Establish the project structure

Suggested structure:

```text
agentfleet/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── orchestration/
│   │   ├── agents/
│   │   ├── tools/
│   │   ├── workers/
│   │   └── events/
│   │
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   │
│   └── migrations/
│
├── frontend/
│
├── evaluation/
│   ├── scenarios/
│   ├── datasets/
│   └── benchmarks/
│
├── docs/
│   ├── architecture/
│   ├── decisions/
│   └── diagrams/
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

The structure may be adjusted as the project grows.

### Step 0.3 — Establish development standards

- Configure formatting and linting.
- Set up pytest.
- Configure environment variables.
- Establish Git branching and commit conventions.
- Add initial CI checks.
- Document local development setup.

**Milestone 0: Foundation ready**

Success criteria:
- Application starts locally.
- Dependencies install correctly.
- Database can be started.
- Tests execute.
- Repository is understandable and documented.

---

# PHASE 1 — Database and core backend

**Objective:** Build the foundation that all subsequent functionality depends on.

### Step 1.1 — Design the database

Identify the main entities and their relationships.

Initial entities:

| Entity | Responsibility |
|---|---|
| User | Application users |
| Agent | Agent configuration and identity |
| WorkflowTemplate | Reusable workflow definitions |
| WorkflowRun | Individual workflow execution |
| Task | Individual workflow operation |
| TaskDependency | Dependencies between tasks |
| ExecutionEvent | Historical execution events |
| Checkpoint | Recoverable execution state |
| Approval | Human approval requests |
| Tool | Available agent capabilities |
| ToolExecution | Record of tool calls |
| AuditLog | Security-sensitive actions |

Create an ER diagram before implementing all the tables.

Consider:
- Primary and foreign keys.
- Indexing.
- Relationships.
- Constraints.
- Timestamps.
- JSON fields where flexible structured data is appropriate.
- Deletion and retention policies.

### Step 1.2 — Implement database integration

- Configure SQLAlchemy.
- Create database models.
- Set up Alembic migrations.
- Establish transaction boundaries.
- Implement database session management.
- Test database connectivity.

### Step 1.3 — Build initial API endpoints

Start with:

```text
POST   /api/workflows
GET    /api/workflows
GET    /api/workflows/{id}

POST   /api/workflows/{id}/runs
GET    /api/runs/{id}

GET    /api/agents
GET    /api/agents/{id}
```

These can initially return simple data without actual agent execution.

### Testing requirements

- Database model tests.
- CRUD integration tests.
- Validation tests.
- Invalid ID handling.
- Transaction rollback tests.
- Migration tests.

**Milestone 1: Functional backend foundation**

Users, agents, workflow templates, and workflow runs can be created and retrieved through the API.

---

# PHASE 2 — Workflow orchestration engine

**Objective:** Build the core execution engine that makes AgentFleet more than a conventional CRUD application.

This is one of the most important phases.

### Step 2.1 — Define workflow structure

A workflow consists of tasks, dependencies, and execution rules.

Example:

```text
Incident Investigation
          |
          ▼
   Gather Evidence
       /      \
      ▼        ▼
 Analyze Logs  Analyze Deployment
      |        |
      └───┬────┘
          ▼
    Compare Findings
          |
          ▼
     Verify Diagnosis
          |
          ▼
    Human Approval
          |
          ▼
   Generate Report
```

Tasks should have:

- Unique identifiers.
- A defined execution type.
- Input and output schemas.
- Dependencies.
- Timeout configuration.
- Retry configuration.
- Execution status.
- Associated agent or tool.

### Step 2.2 — Implement workflow state management

Define explicit lifecycle states.

Workflow:

```text
PENDING
  |
  ▼
RUNNING
  |
  ├── COMPLETED
  ├── FAILED
  ├── CANCELLED
  └── WAITING_FOR_APPROVAL
```

Task:

```text
PENDING
  |
  ▼
QUEUED
  |
  ▼
RUNNING
  |
  ├── COMPLETED
  ├── RETRYING
  ├── FAILED
  └── WAITING_FOR_APPROVAL
```

Define valid state transitions. Prevent invalid transitions, such as completing a task that was never started.

### Step 2.3 — Build the scheduler

Implement functionality that:

- Identifies tasks ready for execution.
- Checks dependency completion.
- Schedules eligible tasks.
- Prevents dependent tasks from running prematurely.
- Tracks active executions.
- Handles workflow completion.

Initially, support sequential execution.

Then introduce parallel execution for independent tasks.

### Step 2.4 — Build the task executor

Create a standardized execution interface.

The orchestrator should not need to know whether a task is:

- An AI agent.
- A normal Python function.
- An external API call.
- A background operation.

Each executor should accept validated input and produce a standardized result.

### Step 2.5 — Introduce background workers

Move execution outside the HTTP request lifecycle.

A user submitting a workflow should receive a run ID immediately rather than waiting for the entire workflow to finish.

Implement:
- Job claiming.
- Worker execution.
- Execution status updates.
- Worker concurrency limits.
- Task timeouts.

**Milestone 2: Working orchestration engine**

A workflow containing multiple tasks can be submitted, executed in dependency order, and its results retrieved.

Use mocked task handlers initially. Real AI integration comes later.

### Testing requirements

- Sequential task execution.
- Parallel independent tasks.
- Dependency enforcement.
- Invalid dependency detection.
- Circular dependency detection.
- Worker concurrency limits.
- State transition validation.
- Task failure handling.

---

# PHASE 3 — Durable execution and failure recovery

**Objective:** Ensure workflows remain reliable even when the application or workers encounter failures.

This is one of the most valuable technical differentiators in the project.

### Step 3.1 — Persist execution progress

Every meaningful state transition should be stored.

Persist:
- Workflow status.
- Task status.
- Execution attempts.
- Start and completion times.
- Task results.
- Checkpoints.
- Failure information.

The database must be authoritative.

### Step 3.2 — Implement checkpointing

Save recoverable execution progress at appropriate boundaries.

For example:

```text
Evidence collection      COMPLETED
Log analysis             COMPLETED
Deployment analysis      COMPLETED
Diagnosis verification   RUNNING
```

If the application restarts, it should not rerun completed work unnecessarily.

### Step 3.3 — Implement retry policies

Support:
- Maximum attempts.
- Exponential backoff.
- Retryable versus permanent errors.
- Per-task retry configuration.
- Maximum execution duration.

For example:

```text
Attempt 1 → Failure
Wait 2 seconds

Attempt 2 → Failure
Wait 4 seconds

Attempt 3 → Success
```

### Step 3.4 — Implement idempotency

This is particularly important.

If a worker crashes after an external action succeeds but before the result is saved, the system may attempt that action again.

Design mechanisms to prevent duplicate side effects.

Examples:
- Idempotency keys.
- Unique operation identifiers.
- Transactional state transitions.
- Deduplication.
- Safe handling of repeated requests.

Do not assume that exactly-once execution is automatically achievable across databases and external APIs. Design for at-least-once delivery with idempotent operations.

### Step 3.5 — Implement worker recovery

Introduce:
- Worker heartbeats.
- Job leases.
- Lease expiration.
- Stale-job detection.
- Recovery of abandoned executions.

A worker should not permanently own a job simply because it crashed.

### Step 3.6 — Implement cancellation

Allow users to cancel workflows.

Handle:
- Pending tasks.
- Running tasks.
- Future scheduled tasks.
- Cancellation requests during execution.

Document how cancellation interacts with already-completed external actions.

### Testing requirements

Simulate:
- Application restart during execution.
- Worker crash.
- Database connection failure.
- Repeated job delivery.
- Timeout.
- Retry exhaustion.
- Duplicate submission.
- Cancellation during execution.

**Milestone 3: Durable orchestration**

Demonstrate that a workflow can survive an application restart and resume without unnecessarily repeating completed operations.

This is a key demonstration scenario for the project.

---

# PHASE 4 — AI agents and tool execution

**Objective:** Integrate real AI agents into the orchestration engine.

The execution engine should already work without an LLM. Now give it intelligent task handlers.

### Step 4.1 — Establish an LLM provider abstraction

Create a common interface for model calls.

Responsibilities:
- Send prompts.
- Supply structured context.
- Handle model responses.
- Validate structured output.
- Track token usage.
- Track latency and cost.
- Handle provider errors.

Avoid scattering provider-specific API calls throughout the application.

### Step 4.2 — Implement agent definitions

Each agent should have:

- Name.
- Description.
- Role.
- System instructions.
- Model configuration.
- Available tools.
- Permission level.
- Input and output schemas.

### Step 4.3 — Build the first specialized agents

For incident investigation:

**Scout Agent**
- Collects relevant logs and deployment events.
- Identifies potentially relevant evidence.

**Analysis Agent**
- Examines the evidence.
- Identifies patterns and possible causes.
- Produces structured hypotheses.

**Verification Agent**
- Challenges proposed explanations.
- Checks whether evidence supports each conclusion.
- Identifies missing information.

**Report Agent**
- Produces a structured final report.
- Summarizes findings and recommended actions.

Do not create agents simply to increase their number. Each should have a distinct responsibility.

### Step 4.4 — Implement tool calling

Tools should be separate from agents.

Example tools:
- Search logs.
- Retrieve deployment history.
- Query simulated metrics.
- Inspect service health.
- Run a predefined diagnostic check.

Each tool needs:
- A defined input schema.
- Validation.
- Authorization.
- Execution timeout.
- Standardized output.
- Error handling.
- Execution logging.

### Step 4.5 — Implement context management

Agents need access to relevant workflow information without passing enormous amounts of unrelated information between every step.

Implement:
- Workflow context.
- Task-specific input.
- Evidence references.
- Previous task outputs.
- Context size limits.
- Structured output validation.

### Step 4.6 — Implement evidence provenance

Every important claim in the final report should reference supporting evidence.

For example:

```text
Finding:
API latency increased following deployment 1.8.4.

Evidence:
- Deployment timestamp: 14:32
- P95 latency increased from 180ms to 920ms
- Database connection pool saturation began at 14:35

Confidence:
High

Alternative explanation:
Increased request volume.
```

The verification agent should distinguish supported conclusions from speculation.

**Milestone 4: Real AI workflow**

A submitted incident is investigated by multiple specialized agents and produces a structured report with supporting evidence.

### Testing requirements

- Mocked LLM responses.
- Invalid structured outputs.
- Provider timeout.
- Rate limiting.
- Tool execution failure.
- Malicious tool arguments.
- Missing evidence.
- Context size limits.
- Agent disagreement.
- Incorrect conclusions.

---

# PHASE 5 — Human approval and security

**Objective:** Make AgentFleet safe enough to demonstrate as a serious software product.

Security should not be treated as a final polish phase. It must be incorporated throughout development, with this phase consolidating the security model.

### Step 5.1 — Authentication

Implement:
- User registration.
- Login.
- Secure session or token management.
- Password hashing if using password authentication.
- Logout and token/session expiration.
- Protected API endpoints.

### Step 5.2 — Authorization

Implement role-based permissions initially.

Example:

| Role | Permissions |
|---|---|
| Admin | Manage agents, tools, workflows and users |
| Operator | Launch and manage workflows |
| Viewer | Inspect executions and reports |

Enforce authorization on the backend, not just by hiding frontend buttons.

Also ensure users can only access resources belonging to their organization or workspace.

### Step 5.3 — Tool security

This is especially important for agent systems.

Implement:
- Tool allowlists.
- Per-agent tool permissions.
- Strict argument validation.
- Execution timeouts.
- Output size limits.
- Rate limits.
- Restricted network access where applicable.
- No arbitrary shell execution.
- No unrestricted filesystem access.

Treat agent-generated arguments and external content as untrusted input.

### Step 5.4 — Human approval system

Some tools should require approval before execution.

Example:

```text
Agent proposes remediation
           |
           ▼
    Approval requested
           |
      ┌────┴────┐
      ▼         ▼
   Approved   Rejected
      |         |
      ▼         ▼
 Execute     Stop / Revise
```

Implement:
- Approval requests.
- Approval status.
- User identity.
- Approval timestamps.
- Expiration.
- Rejection reasons.
- Audit records.

The workflow should be able to pause and resume without losing its execution context.

### Step 5.5 — Security hardening

Address:
- Secret management.
- SQL injection.
- Cross-site scripting.
- CSRF where relevant.
- CORS configuration.
- Authentication brute-force protection.
- Sensitive information in logs.
- Prompt injection.
- Untrusted document and log content.
- Insecure direct object references.
- Dependency vulnerabilities.

Do not treat an agent's interpretation of external logs or documents as trusted instructions.

### Security milestone

Create a dedicated security checklist and verify it before public deployment.

**Milestone 5: Secure multi-user application**

Users can authenticate, access only authorized resources, control agent permissions, and approve sensitive operations.

### Testing requirements

- Unauthenticated access.
- Unauthorized resource access.
- Cross-user data isolation.
- Invalid tokens.
- Expired sessions.
- Invalid tool arguments.
- Prompt injection attempts.
- Approval authorization.
- Audit log integrity.
- Secret leakage checks.

---

# PHASE 6 — Observability and real-time frontend integration

**Objective:** Make execution understandable and visually engaging.

This is where the product starts feeling like a real operations platform.

### Step 6.1 — Build the event system

Generate structured events for meaningful execution changes.

Examples:

```text
workflow.created
workflow.started
task.queued
agent.started
tool.called
tool.completed
task.failed
task.retrying
approval.requested
approval.granted
workflow.completed
```

Persist these events so execution history can be reconstructed.

### Step 6.2 — Implement execution traces

Each workflow should have a trace containing:

- Workflow ID.
- Task ID.
- Agent ID.
- Execution attempt.
- Start/end timestamps.
- Inputs and outputs.
- Tool calls.
- Errors.
- Token usage.
- Model/provider.
- Estimated cost.

Use correlation IDs to connect events across a workflow.

Be careful not to expose secrets, authentication tokens, or sensitive personal information in traces.

### Step 6.3 — Implement live event streaming

Use SSE or WebSockets.

The frontend should receive:
- Workflow state changes.
- Agent activity.
- Task progress.
- Tool execution results.
- Errors.
- Approval requests.

Support reconnecting and catching up using persisted event IDs. Do not rely exclusively on an in-memory event stream.

### Step 6.4 — Build the main dashboard

Suggested pages:

**Fleet Overview**
- Active workflows.
- Available agents.
- Agent health.
- Recent activity.
- Success/failure statistics.

**Workflow Builder**
- Create workflows.
- Define agents.
- Connect task dependencies.
- Configure execution options.

**Live Operations**
- Active workflow graph.
- Agent status.
- Execution timeline.
- Current task.
- Resource usage.

**Execution Inspector**
- Full task history.
- Inputs and outputs.
- Tool calls.
- Errors.
- Retry history.
- Token usage and cost.

**Approvals**
- Pending approvals.
- Proposed actions.
- Supporting information.
- Approve/reject controls.

**Analytics**
- Workflow success rates.
- Average execution time.
- Cost per workflow.
- Agent performance.

### Step 6.5 — Visual identity

Use a restrained sci-fi command-center theme.

Design principles:
- Dark navy/charcoal foundation.
- Teal/cyan active states.
- Amber warnings.
- Red failure states.
- Clean typography.
- Restrained glow and animation.
- Highly readable technical data.
- Consistent spacing and component design.

The interface should look like professional developer tooling, not a video game menu.

**Milestone 6: Complete interactive application**

A user can launch an investigation and watch it progress live, inspect its execution history, and interact with approval requests.

---

# PHASE 7 — Evaluation and quality measurement

**Objective:** Demonstrate that the system can measure whether its agents are actually useful.

This is an important differentiator between an AI demo and an engineered AI product.

### Step 7.1 — Create evaluation scenarios

Create a fixed dataset of simulated incidents.

Examples:

1. Database connection pool exhaustion.
2. Increased API latency after deployment.
3. Memory leak in an application service.
4. Elevated error rate caused by a dependency.
5. Increased request volume.
6. Failed background processing jobs.

Each scenario should have:
- Ground-truth cause.
- Supporting evidence.
- Expected diagnosis.
- Relevant logs and metrics.
- Expected recommendations.

### Step 7.2 — Build evaluation execution

Allow the same scenario to run repeatedly.

Record:
- Correct diagnosis.
- Evidence coverage.
- Unsupported claims.
- Completion rate.
- Execution time.
- Token consumption.
- Estimated cost.

### Step 7.3 — Compare models and prompts

Allow controlled comparisons.

For example:
- Model A vs Model B.
- Prompt version 1 vs Prompt version 2.
- Single-agent vs multi-agent workflow.

Keep other variables consistent where possible.

### Step 7.4 — Build regression testing

Run evaluation scenarios after changing:
- Agent instructions.
- Models.
- Tool implementations.
- Workflow architecture.

Use a mixture of deterministic assertions and model-based quality evaluations. Avoid relying entirely on another LLM to judge an LLM.

**Milestone 7: Reproducible agent evaluation**

Measurable improvements or regressions in agent quality, cost, and performance can be demonstrated.

---

# PHASE 8 — Performance and scalability

**Objective:** Understand and document how the backend behaves under load.

### Step 8.1 — Establish benchmarks

Measure:
- Workflow creation latency.
- Task scheduling latency.
- Event delivery latency.
- Workflow completion time.
- Concurrent execution capacity.
- Database query performance.
- Worker utilization.

### Step 8.2 — Introduce resource limits

Implement:
- Maximum active workflows.
- Per-user concurrency limits.
- Per-agent concurrency limits.
- API rate limits.
- Model request budgets.
- Maximum workflow duration.
- Maximum retry count.

### Step 8.3 — Optimize bottlenecks

Use actual profiling and benchmark results.

Potential areas:
- Database indexes.
- Connection pooling.
- Query optimization.
- Worker concurrency.
- Event delivery.
- Caching.
- Payload sizes.

### Step 8.4 — Test failure under load

Simulate:
- Worker overload.
- Database slowdowns.
- Provider rate limiting.
- Large workflow volumes.
- Repeated failures.
- Multiple concurrent users.

**Milestone 8: Performance report**

Publish actual benchmark results, testing methodology, hardware/configuration, limitations, and identified bottlenecks.

---

# PHASE 9 — Docker, CI/CD and deployment

**Objective:** Turn the project into an accessible, reproducible application.

### Step 9.1 — Containerize

Create Docker configurations for:
- Backend API.
- Worker.
- Frontend.
- PostgreSQL.
- Redis if used.

Use Docker Compose for local development.

### Step 9.2 — Establish CI

GitHub Actions should run:
- Formatting checks.
- Linting.
- Type checks where applicable.
- Unit tests.
- Integration tests.
- Migration checks.
- Security/dependency checks.

### Step 9.3 — Deploy

Deploy:
- Frontend.
- Backend API.
- Background workers.
- PostgreSQL database.
- Redis if required.

Use managed services where practical.

### Step 9.4 — Production configuration

Implement:
- Environment-specific configuration.
- Secret management.
- HTTPS.
- Database backups.
- Health checks.
- Structured logs.
- Error reporting.
- Monitoring.
- Database migration procedures.

### Step 9.5 — Public demo mode

Provide a preconfigured demonstration account or demo environment.

Use synthetic data and simulated tools.

Visitors should be able to:
- Launch an example investigation.
- Watch it execute.
- Inspect a completed run.
- View a sample evaluation report.

Protect the public demo with execution quotas and strict tool restrictions.

**Milestone 9: Publicly accessible application**

A hiring manager can access and explore the application without needing to install or configure anything.

---

# PHASE 10 — Portfolio presentation

**Objective:** Make the project and its engineering decisions easy for visitors and technical reviewers to understand.

### Step 10.1 — README

Include:
- Product overview.
- Problem being solved.
- Screenshots.
- Feature list.
- Technology stack.
- Architecture diagram.
- Setup instructions.
- Demo link.
- Testing instructions.
- Known limitations.

### Step 10.2 — Architecture documentation

Explain important decisions.

Examples:

- Why PostgreSQL is the source of truth.
- Why the worker architecture was selected.
- How task dependencies are represented.
- How concurrent execution works.
- How workflow recovery works.
- How duplicate execution is prevented.
- How permissions are enforced.
- How events are delivered.
- How agent outputs are evaluated.

### Step 10.3 — Architecture Decision Records

Document major decisions as short ADRs.

For example:

```text
ADR-001: PostgreSQL as workflow state store

Context:
Workflow execution must survive restarts.

Decision:
Persist workflow and task state in PostgreSQL.

Alternatives:
Redis-only state management.
External workflow engine.

Trade-offs:
More database coordination and implementation
complexity, but durable state and transactional
consistency for the initial application.
```

### Step 10.4 — Demo video

Create a 2–4 minute walkthrough.

Suggested sequence:

1. Introduce the problem.
2. Launch an incident investigation.
3. Show agents executing concurrently.
4. Demonstrate a simulated failure and retry.
5. Show a human approval request.
6. Display the final report.
7. Inspect execution traces and performance metrics.

**Milestone 10: Portfolio-ready project**

A deployed, documented, tested application with a clear technical story.

---

# 5. Testing strategy — requirements throughout development

Testing should not be saved for the end.

Use the following testing layers:

| Test type | What it verifies |
|---|---|
| Unit | Individual functions, services and business rules |
| Integration | Database, worker, API and external-service interactions |
| End-to-end | Complete user workflows |
| Failure injection | Recovery from crashes and errors |
| Security | Authorization, input validation and isolation |
| Performance | Throughput, latency and concurrency |
| Evaluation | Agent correctness and output quality |

## Essential end-to-end test scenarios

These are particularly important:

1. A user submits a workflow and receives a run ID.
2. Multiple independent tasks execute concurrently.
3. A dependent task waits until its prerequisites complete.
4. An agent returns an invalid structured response.
5. A tool call times out.
6. A task fails and successfully retries.
7. A worker crashes during execution.
8. The application restarts and recovers the workflow.
9. A duplicate task delivery does not cause duplicate side effects.
10. A workflow pauses for human approval.
11. An unauthorized user attempts to access another user's workflow.
12. A workflow completes and produces a report with traceable evidence.

The primary demonstration should include several of these scenarios, not just the happy path.

---

# 6. Security milestones

Security should be treated as a continuous requirement.

| Development stage | Security requirement |
|---|---|
| Foundation | Secrets, environment configuration, dependency hygiene |
| Database/API | Input validation, safe queries, request validation |
| Orchestration | Execution limits, timeout enforcement, safe state transitions |
| AI integration | Prompt injection defenses, output validation, tool restrictions |
| Multi-user | Authentication, authorization, resource isolation |
| Human approval | Approval authorization, audit history, safe action execution |
| Deployment | HTTPS, secret management, backups, monitoring |
| Public demo | Synthetic data, quotas, restricted tools, abuse protection |

**Important:** Never expose an unrestricted shell, arbitrary Python execution, or unrestricted filesystem access to an LLM-controlled agent in this project.

---

# 7. Delivery approach

Work proceeds in small slices of roughly 2-4 hours, each producing a testable improvement and a short build note in `docs/slices/`. The quality of the finished product matters more than completing every optional feature.

If time becomes constrained, prioritize the working product, durable execution, observability, security, and deployment before advanced benchmarking or optional UI features (see section 9).

---

# 8. Definition of done

AgentFleet should not be considered finished merely because agents can communicate with one another.

The project is ready to present when it satisfies these requirements.

## Core product
- [ ] User can submit an incident investigation.
- [ ] Workflow is created and persisted.
- [ ] Multiple specialized agents execute tasks.
- [ ] Task dependencies are respected.
- [ ] Independent tasks can execute concurrently.
- [ ] Final report includes evidence and recommendations.

## Backend engineering
- [ ] Clean modular architecture.
- [ ] Database migrations.
- [ ] Background workers.
- [ ] Durable workflow state.
- [ ] Retry and timeout handling.
- [ ] Checkpointing and recovery.
- [ ] Idempotent task handling.
- [ ] Cancellation support.

## AI engineering
- [ ] Structured agent outputs.
- [ ] Controlled tool execution.
- [ ] Provider abstraction.
- [ ] Evidence provenance.
- [ ] Human approval.
- [ ] Evaluation scenarios.
- [ ] Cost and latency tracking.

## Security and reliability
- [ ] Authentication.
- [ ] Authorization.
- [ ] User data isolation.
- [ ] Tool permission restrictions.
- [ ] Audit history.
- [ ] Input validation.
- [ ] Security testing.
- [ ] Failure recovery tests.

## Product and deployment
- [ ] Polished interactive dashboard.
- [ ] Live execution updates.
- [ ] Workflow visualization.
- [ ] Execution inspector.
- [ ] Dockerized application.
- [ ] Automated CI.
- [ ] Public deployment.
- [ ] Demo workflow.
- [ ] Documentation.
- [ ] Video walkthrough.

---

# 9. What to prioritize if the project grows too large

The most important thing is to avoid building a platform that is 70% complete but never becomes a usable product.

Use these priorities:

**P0 — Essential**
- Complete incident investigation workflow.
- Persistent backend state.
- Task scheduling and dependencies.
- AI agent execution.
- Basic retries and recovery.
- Execution history.
- Working frontend.
- Automated tests.
- Deployment.

**P1 — Major differentiators**
- Concurrent workers.
- Worker recovery.
- Checkpointing.
- Idempotency.
- Human approval.
- Tool permissions.
- Detailed traces.
- Evaluation framework.

**P2 — Additional polish**
- Advanced analytics.
- Model comparisons.
- Performance benchmarks.
- Workflow templates.
- Advanced workflow editor.
- More sophisticated resource scheduling.

Do not start P2 while P0 is unfinished.

---

# 10. Project goals

AgentFleet should demonstrate that a complex software problem can be taken from concept to production, with the reasoning documented along the way. The project should be explainable and defensible on:

1. How the underlying problem was identified.
2. How it was translated into product requirements.
3. How the database and application architecture were designed.
4. How asynchronous processing was implemented.
5. How concurrency and failure recovery are handled.
6. How AI agents and external tools are integrated.
7. How execution is made secure and observable.
8. How the system is tested under normal and abnormal conditions.
9. How the application is deployed and monitored.
10. What would change to support substantially more users and workloads.
