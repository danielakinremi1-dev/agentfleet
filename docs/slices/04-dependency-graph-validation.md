# Slice 04: Dependency graph validation

## Goal
Start Phase 1: design the run lifecycle, and guarantee that a workflow template's dependencies can
always be satisfied, by rejecting any template whose task graph contains a cycle.

## What was built
- **Design doc [0001: run lifecycle](../design-docs/0001-run-lifecycle.md):** dependency graph validation,
  run creation as one transaction, the run and task state machines, their failure modes, and the
  alternatives considered. It is the design for all four slices of Phase 1.
- **`app/orchestration/dag.py`:** `topological_order(dependencies)` returns the tasks in an order in which
  each comes after everything it depends on. `CycleError` carries one concrete cycle.
- **Template validation:** `WorkflowDefinition` calls `topological_order`, so `POST /api/workflows` returns
  `422` for a cyclic definition. A dependency listed twice on one task is also rejected.

| Request | Before | Now |
|---|---|---|
| Template where `a` depends on `b` and `b` on `a` | `201`, stored | `422`, `dependency cycle: a -> b -> a` |
| Task with `depends_on: ["a", "a"]` | `201`, stored | `422`, `lists the same dependency more than once` |

## How it works
**Ordering (Kahn's algorithm).** Count each task's unmet dependencies. Repeatedly take a task with none,
append it to the result, and reduce the count of every task that depends on it; a task that reaches zero
becomes available. For the diamond-shaped graph below:

```text
            gather
           /      \
  analyze_logs   analyze_deploy
           \      /
           compare
```

| Step | Ready queue | Emitted | Counts afterwards |
|---|---|---|---|
| Start | `gather` | | `analyze_logs` 1, `analyze_deploy` 1, `compare` 2 |
| 1 | `analyze_logs`, `analyze_deploy` | `gather` | `compare` 2 |
| 2 | `analyze_deploy` | `analyze_logs` | `compare` 1 |
| 3 | `compare` | `analyze_deploy` | |
| 4 | | `compare` | |

All four tasks were emitted, so the order is valid.

**Detecting a cycle.** If the queue empties while tasks remain, each remaining task is waiting on another
remaining task. That is only possible when a cycle exists, because in an acyclic graph some task always
has nothing left to wait for.

**Naming the cycle.** The remaining ("blocked") tasks are those on a cycle and those downstream of one.
Starting from the first blocked task in definition order, the code steps to a dependency that is also
blocked, and repeats. Such a dependency always exists, so the walk must revisit a task; the path between
the two visits is the cycle, and anything before it is dropped.

```text
report ──► c ──► b ──► a ──► c     walk:  report, c, b, a, then c again
          └──────cycle──────┘      cycle: c -> b -> a -> c      ("report" is not on it)
```

**In the request path.** The check runs inside Pydantic validation, before the route or service is
called. `CycleError` subclasses `ValueError`, which Pydantic converts into a validation error, so FastAPI
returns `422` and nothing is written to the database.

```json
{
  "type": "value_error",
  "loc": ["body", "definition"],
  "msg": "Value error, dependency cycle: gather -> report -> analyze -> gather (each task depends on the next)"
}
```

## Why this approach
- Validating at write time, Kahn's algorithm, naming one concrete cycle and rejecting repeated
  dependencies: [ADR-0008](../decisions/0008-dependency-graph-validation.md).
- The module imports nothing from the database, FastAPI or Pydantic. It is tested without any setup and
  will be reused by the scheduler in Phase 2.
- The implementation is iterative. A recursive search fails on a chain deeper than Python's recursion
  limit; a test with a 5,000-task chain covers this.
- The order is deterministic (definition order among ready tasks), so tests and later API responses do not
  vary between runs.

## Technologies introduced
None.

## Tests
152 tests in total (118 added), 100% branch coverage of `app/`.

**Unit: `tests/unit/test_dag.py`**

| Test | Failure it catches |
|---|---|
| Empty graph, single task | Edge cases that crash on an empty queue or a missing key |
| Chain defined backwards | Treating definition order as execution order |
| Diamond | Emitting a join task after only one of its branches |
| Disconnected tasks keep definition order; repeated calls agree | Non-deterministic output |
| Repeated dependency counts once | A task left waiting forever, reported as a false cycle |
| 5,000-task chain | A recursive implementation exhausting the call stack |
| Two-task, self and five-task cycles | A cycle going undetected, or reported incompletely |
| Cycle with a downstream task | Blaming a task that is blocked by the cycle but not on it |
| Cycle among otherwise valid tasks | Reporting tasks outside the cycle |
| Unknown dependency | Confusing a missing task with a cycle |
| 50 seeded random acyclic graphs | Any ordering that violates the definition of a topological order |
| 50 seeded random graphs with one back edge | A reported "cycle" that is not a real path in the graph |

The random graphs are generated from fixed seeds, so they are reproducible, and each result is checked
against the definition (every task once, after its dependencies; every reported edge exists) rather than
against a hand-written expected value.

**Unit: `tests/unit/test_workflow_definition.py`**: a two-task cycle, a cycle with a downstream task and a
repeated dependency are rejected by the schema with the expected message.

**Integration: `tests/integration/test_workflow_templates_api.py`**: a cyclic template returns `422` naming
the cycle, and the template list is still empty afterwards.

No failure-injection tests: this slice adds no durability feature.

## Follow-ups
- Run creation re-validates the stored definition (ADR-0008, decision 2); templates stored before this
  slice are not otherwise re-checked.
- The cycle also appears as a list under `ctx.error.cycle` in the `422` body. That is a side effect of how
  FastAPI serializes the exception, not a contract; the uniform error format later in Phase 1 defines the
  response shape deliberately.
- Next slice: run creation (migration `0002`, `task_dependencies`, `create_run`).
