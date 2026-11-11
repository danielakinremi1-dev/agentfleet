# ADR-0009: Run materialization

Status: accepted

## Context
A workflow template stores its task graph as one JSONB document
([ADR-0003](0003-initial-data-model.md)). To execute a template, workers must be able to lock, update and
query tasks one at a time, and the scheduler must be able to ask which tasks wait for which. Neither is
possible against a document. Creating a run therefore has to turn the document into rows
("materialize" it), and it has to do so without ever leaving a partly built run behind. The overall design
is in [design doc 0001](../design-docs/0001-run-lifecycle.md); this record fixes the decisions taken while
implementing it, including two changes to that design.

## Decision
1. **A run is a snapshot made of rows.** Creating a run inserts one `workflow_runs` row, one `tasks` row
   per definition entry and one `task_dependencies` row per dependency. Each task copies its key and name
   from the definition. The run keeps `template_id` for provenance and never reads the template again.
2. **One transaction.** The three inserts are flushed in dependency order and committed together, before
   the service returns ([ADR-0004](0004-session-and-transaction-boundaries.md)). A failure at any point
   leaves no rows.
3. **IDs are generated in the application.** The key-to-ID mapping is built in memory, so dependency rows
   are constructed without reading the inserted tasks back. The mapping is a pure function
   (`materialize`), separate from the code that writes.
4. **Composite foreign keys keep an edge inside one run.** `task_dependencies` has a single `run_id` column
   that takes part in both foreign keys, `(run_id, task_id)` and `(run_id, depends_on_task_id)`, each
   referencing `tasks (run_id, id)`. An edge between tasks of different runs cannot be stored. This requires
   a unique constraint on `tasks (run_id, id)`, which is redundant for uniqueness (`id` is the primary key)
   and exists only as the reference target.
5. **Tasks record their definition order in `tasks.position`**, unique within a run. *This is an addition
   to design doc 0001.* All rows of a run are inserted in one transaction and share one `created_at`, so
   without it tasks have no stable order. Dependency lists in responses are ordered by the position of the
   task depended on, so creating a run and reading it return the same representation.
6. **The template row is read `FOR KEY SHARE`.** *This replaces the behaviour described in design doc
   0001*, which let the insert fail its foreign key and reported `404`. The lock is the one PostgreSQL takes
   for the foreign key check on insert, taken one statement earlier. It conflicts only with deleting the
   row or changing its key, so concurrent run creations and ordinary reads are not blocked, and the
   template cannot disappear between being read and being referenced.
7. **The stored definition is validated again** ([ADR-0008](0008-dependency-graph-validation.md), decision
   2). If it is not a valid graph the request is refused with `409 Conflict`: the request is well-formed,
   and it conflicts with the state of the template.
8. **Everything starts `pending`, and nothing is queued.** Deciding which tasks are ready belongs to the
   scheduler (Phase 2), so the readiness rule exists in one place.
9. **Run input is a JSON object of at most 64 KiB** (measured as compact UTF-8 JSON). Values that parse
   but cannot be stored in `jsonb` (NaN, Infinity and the NUL character) are rejected with `422`.

## Alternatives considered
- **Keep the graph as JSON on the run and interpret it at run time.** No materialization step, but no row
  locks per task, no foreign keys, and no index for "which tasks wait for this one".
- **Single-column foreign keys from each end of an edge to `tasks.id`.** Simpler, but an application bug
  could link tasks of two runs, and the scheduler would then wait on another run's task. The composite
  keys cost one redundant unique index on `tasks`.
- **Order tasks by key, or compute a topological order on every read.** Needs no column. Ordering by key
  loses the author's order; ordering at read time repeats work on every request and still needs a
  tie-break rule. A stored position is one integer per task and is also available to the scheduler as a
  deterministic tie-break.
- **No lock; translate the foreign key violation into `404`.** Also correct, since the foreign key
  guarantees that no run references a missing template. It adds an error-translation branch that can only
  be exercised by simulating the race, whereas the lock removes the race itself.
- **`FOR SHARE` or `FOR UPDATE` on the template.** Both are stronger than needed. `FOR UPDATE` would make
  concurrent run creations of one template wait for each other.
- **`422` or `500` for an invalid stored definition.** `422` describes a problem with the request body,
  which here is valid. `500` would hide a condition the client can understand and act on.
- **Queue tasks without dependencies at creation.** Saves one scheduler pass and puts the readiness rule in
  two places.
- **ORM relationships (`run.tasks`, `task.dependencies`) with eager loading.** Fewer lines in the read
  path, but the queries become implicit, and async SQLAlchemy forbids lazy loading. Three explicit queries
  are easier to reason about and to profile.

## Consequences
- A run is either fully present (run, all tasks, all edges) or absent. Tests inject a failure at each
  insert and verify that nothing remains.
- Changing or deleting a template can never alter an existing run's graph.
- Reading a run costs three indexed queries. `task_dependencies` has no index on `run_id` alone; edges are
  read by `task_id`, the leading column of the primary key.
- Run creation is not idempotent: a client that retries after losing the response creates a second run.
  Idempotency keys are added in Phase 3.
- The size limit applies after the body has been parsed. A limit on raw request size belongs to the
  reverse proxy introduced with deployment (Phase 7).
- Migration `0002` numbers existing tasks before making `position` required, so it applies to a database
  that already holds tasks.
