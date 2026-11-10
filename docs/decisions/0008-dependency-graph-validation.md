# ADR-0008: Dependency graph validation

Status: accepted

## Context
A workflow template lists tasks and, for each, the tasks it depends on. Architecture principle 4 requires
explicit dependencies that form a directed acyclic graph. Until this slice, a template was checked for
unique keys, known dependencies and self-dependencies, but a longer cycle (`a` waits for `b`, `b` waits
for `a`) was accepted. Such a template can be stored and instantiated, and its run would never finish:
each task on the cycle waits for another. The design is described in
[design doc 0001](../design-docs/0001-run-lifecycle.md).

## Decision
1. **Validate when the template is stored.** The check is part of `WorkflowDefinition` validation, so a
   cyclic template is rejected at the API boundary with `422` and never reaches the database.
2. **Validate again when a run is created** (implemented with run creation). Definitions are stored as
   JSONB, which the database cannot check for cycles, so a definition stored before this check existed or
   edited by hand is not trusted.
3. **Kahn's algorithm**, implemented in `app/orchestration/dag.py` as a pure function that returns a
   topological order.
4. **The error names one concrete cycle**, as an ordered list of task keys that starts and ends with the
   same task, found by walking dependency edges among the tasks that could not be ordered.
5. **The order is deterministic**: tasks that are ready at the same time keep their definition order.
6. **A dependency listed twice on one task is rejected**, because an edge will be a primary key in
   `task_dependencies` and can exist only once.

## Alternatives considered
- **Depth-first search with three colours.** Detects a cycle and yields it directly from the recursion
  stack. Not chosen: the natural implementation is recursive and limited by the call stack, and it does
  not produce the topological order as a by-product. Kahn's rule ("ready when nothing it depends on is
  unfinished") is also the rule the scheduler applies at run time, so the two are explained once.
- **Reporting only that a cycle exists, or the set of all blocked tasks.** Simpler, but the blocked set
  includes tasks that are merely downstream of the cycle, which points the template author at tasks that
  are not at fault.
- **Validating only at run creation.** An invalid template would be accepted and fail later, far from the
  request that introduced the problem.
- **A graph library such as NetworkX.** Correct and well tested, but a large dependency for about forty
  lines, and the project implements its own scheduling logic by design (principle 10).
- **Enforcing acyclicity in the database** with a trigger and a recursive query. Guards against writers
  that bypass the application, at the cost of logic in two languages. Not needed for templates, whose
  graph is a single JSON document written through one code path.

## Consequences
- No cyclic template can be created through the API, and the error says which tasks to fix.
- The topological order is available to later code (run creation, scheduler tests, the UI's graph layout)
  without another algorithm.
- Templates already stored are not re-checked until a run is created from them.
- Validation cost is linear in tasks plus dependencies; with the 100-task limit it is negligible.
