# Slice 02: Delivery workflow

## Goal
Make the delivery process enforceable and repeatable: one command interface for every developer
task, CI that runs the same commands, a protected `main`, and a defined shape for pull requests
and releases.

## What was built
- **`Makefile`:** `setup`, `install`, `up`, `down`, `migrate`, `migration`, `migration-check`, `run`,
  `lint`, `format`, `format-check`, `typecheck`, `test`, `coverage`, `check`, `help`.
- **Coverage gate:** `pytest-cov` measures branch coverage of `app/`; `make coverage` fails below 90%.
- **CI (`.github/workflows/ci.yml`):** every step is a Makefile target; a 10-minute job timeout was added.
- **Branch protection on `main`:** pull request required, `backend` status check required, administrators
  included, force pushes and deletion blocked.
- **`.github/pull_request_template.md`:** summary, how to verify, checklist, open questions.
- **`.github/dependabot.yml`:** monthly grouped update PRs for Python dependencies and GitHub Actions.
- **`CONTRIBUTING.md`:** the workflow from branch to release. **`CHANGELOG.md`:** Keep a Changelog format.

## How it works
**One definition per check.** A check such as linting is defined once, as a Makefile target. A developer
runs `make lint`; CI runs `make lint`. `make check` chains the targets in the order CI runs them, so a
local pass predicts a CI pass.

```text
developer:  make check ──┐
                         ├──► lint → format-check → typecheck → migrate → migration-check → coverage
CI job:     make <step> ─┘
```

**The path to `main`.**

```text
slice branch ──commits──► pull request ──► CI job "backend" ──pass──► merge commit on main
                                                   │
                                                 fail ──► merge blocked by the branch rule
```

**Migration IDs.** `make migration m="..."` asks Alembic to autogenerate a revision and assigns the next
sequential ID (`0002`, `0003`, ...) by counting existing revision files, so migrations sort in order.

**Coverage and async code.** SQLAlchemy's async layer runs database driver calls inside greenlets.
Coverage is configured with `concurrency = ["greenlet", "thread"]` so lines after an awaited database
call are attributed correctly.

## Why this approach
- Protected `main`, one PR per slice, merge commits, phase releases and the 90% threshold:
  [ADR-0006](../decisions/0006-delivery-workflow.md).
- The coverage threshold is below the current figure (100%) so that it fails on a real drop without
  forcing tests for process entry points and signal handlers later.
- Dependabot updates are grouped and monthly to limit review load for a single maintainer.

## Technologies introduced
[GNU Make](../technology-guide.md#gnu-make), [pytest-cov](../technology-guide.md#pytest-cov-coveragepy),
[Dependabot](../technology-guide.md#dependabot).

## Tests
No application behaviour changed; the 34 existing tests pass under `make check` locally and in CI, with
100% branch coverage of `app/` (222 statements, 12 branches).
Verified by hand: `make check` passes from a clean state, the migration ID helper yields `0002`, and the
protection rule on `main` reads back from the GitHub API with the settings listed above.

## Follow-ups
- The application version is written in two places (`backend/pyproject.toml` and `app/main.py`); read it
  from package metadata before the first release bump.
- Add an image build step to CI when the API and worker Dockerfile is introduced.
- Add dependency vulnerability scanning (`pip-audit`) with the security hardening work.
- Turn on required approvals and the up-to-date requirement if collaborators join.
