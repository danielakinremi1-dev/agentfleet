# Slice 03: Roadmap restructure

## Goal
Review the plan after the first slice and reshape it so that the backend engineering is built first,
progress is checkable, and the project is presentable at the end of every phase.

## What was built
- **`docs/roadmap.md`**, rewritten: a status summary, progress table with release tags, priorities and
  cut order, and eleven phases that each have a start-of-phase summary, slices as checkboxes, exit
  criteria and an end-of-phase review. Phases 1 and 2 have step-level checklists.
- **`docs/architecture/README.md`**: the living architecture overview: layers and their rules, the request
  lifecycle, the data model, and a table mapping each guarantee to its mechanism and test.
- **`docs/design-docs/README.md`**: when a design doc is required, how it differs from an ADR, the template
  and an index of the six planned docs.
- **ADR-0007**: the reasons for the new order and priorities.
- **README**: capability status table, engineering practices and a reorganized documentation index.
- **`CLAUDE.md`**: process rules for phase starts and ends and for design docs; revised scope guard.
- **`CHANGELOG.md`**: the `0.1.0` section for Phase 0.
- `docs/design/` renamed to `docs/ui-design/` so it is not confused with design docs.

## How it works
**Plan structure.** Work is organized at three levels, each with a fixed completion signal:

```text
Phase  (a capability)   ──► end-of-phase review + changelog section + release tag
  Slice (2-4 hours)     ──► one pull request + one slice note
    Step (a checkbox)   ──► one commit
```

**Phase order.**

```text
0 Foundation ► 1 Workflow core ► 2 Execution engine ► 3 Durable execution     (checkpoint A)
► 4 Agents and tools ► 5 Security and approval ► 6 Observability and UI
► 7 Deployment (checkpoint B) ► 8 Evaluation ► 9 Performance ► 10 Presentation (checkpoint C)
```

Compared with the original plan: durable execution is part of the minimum project; entities are created
when a feature needs them; events are persisted from Phase 2 and streamed in Phase 6; deployment moved
ahead of evaluation and performance; the frontend was reduced to three views.

**Rolling detail.** Only the next two phases carry step checklists. Later phases list slices, and their
steps are written when the phase starts.

## Why this approach
- Ordering, priorities and the alternatives considered: [ADR-0007](../decisions/0007-roadmap-restructure.md).
- The architecture overview pairs every guarantee with a test so that claims in the documentation are
  checkable against the code.
- Design docs are limited to core subsystems to keep the documentation load proportionate.

## Technologies introduced
None. The architecture overview uses Mermaid diagrams, which GitHub renders from Markdown.

## Tests
No application behaviour changed. `make check` passes: 34 tests, 100% branch coverage of `app/`.
Phase and slice references in earlier documents and code comments were updated to the new numbering.

## Follow-ups
- Tag `v0.1.0` and publish the release after this slice is merged.
- Choose a license (the remaining Phase 0 item).
- Phase 1 begins with design doc 0001 (run lifecycle and state machines).
