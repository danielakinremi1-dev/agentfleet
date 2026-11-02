# Product brief

AgentFleet is a platform for creating, executing, monitoring and evaluating multi-step AI
workflows. Users deploy specialized AI agents to complete complex tasks while keeping control
over execution, permissions, costs and outcomes.

## First use case: incident investigation
A user submits an incident, for example:

> Our API latency increased significantly following the latest deployment. Investigate the
> cause, gather supporting evidence, and recommend a remediation.

AgentFleet coordinates specialized agents that investigate, use controlled tools, analyze
evidence, challenge possible explanations, and produce a final report.

## What the platform manages
- Which agents run, and in what order.
- Which tasks can run concurrently.
- What information passes between agents.
- How execution progress is persisted.
- What happens when an agent fails.
- When human approval is required.
- How much time and money a workflow consumes.
- Whether the final result is supported by evidence.

## Four emphases
1. **Durable execution**: workflows survive restarts, failures, retries and worker crashes.
2. **Agent observability**: inspect every decision, tool call, input, output, token cost and event.
3. **Reliability and safety**: idempotency, permission boundaries, approvals, audit trails, recovery.
4. **Evaluation**: replay standardized incidents and measure whether agents find the correct cause.

## Central engineering objective
A reliable backend orchestration system that executes long-running workflows, recovers from
failures, and gives complete visibility into what happened. Incident investigation is the first
use case, not the limit of the platform.

## Primary demo journey
Open the dashboard, pick the Incident Investigation template, submit an incident, watch agents
run live, see a failure and retry, review and approve a proposed remediation, read the
evidence-backed report, and inspect the full trace, cost and performance.
