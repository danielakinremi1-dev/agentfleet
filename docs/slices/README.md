# Slice notes

One file per completed slice, named `NN-short-name.md` (for example `01-foundation.md`).
Together they are the step-by-step build record of the system.

## Template

```markdown
# Slice NN: <name>

## Goal
What this slice set out to deliver.

## What was built
Components, endpoints, tables, modules added or changed.

## How it works
Short walkthrough of the important flow(s) and data model.

## Why this approach
Key design choices, with links to ADRs and technology-guide entries.

## Technologies introduced
Links to technology-guide entries.

## Tests
What is covered and why; any failure-injection tests.

## Follow-ups
Known limitations, deferred refactors, and next steps.
```

## Index
1. [Backend scaffold](01-backend-scaffold.md): project tooling, PostgreSQL, first schema,
   workflow template endpoints, CI.
