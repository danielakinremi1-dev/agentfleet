# ADR-0006: Delivery workflow and quality gates

Status: accepted

## Context
The repository is public and developed by one maintainer. After slice 1, `main` could be pushed to
directly without CI running, the checks existed only as commands typed into the CI workflow, and
"done" for a slice was a convention rather than something enforced. The project is meant to show
how production software is delivered, so the delivery process is part of the product.

## Decision
1. **`main` is protected.** Changes arrive only through pull requests, including for administrators.
   The `backend` CI job is a required status check. Force pushes and deletion are blocked.
   Required approvals are zero: with one maintainer, self-approval is impossible, so the automated
   gate is the enforced part of review.
2. **One pull request per slice**, opened from a `slice/<n>-<name>` branch, described with a template
   that includes verification steps, a checklist and open questions.
3. **Merge commits, not squash merges.** Slices are built as small Conventional Commits, one per step.
   A merge commit keeps that history and marks the slice boundary.
4. **A Makefile is the single command interface.** Every check is a named target, and CI calls the
   same targets, so there is one definition of each check.
5. **Coverage is gated.** `pytest-cov` measures branch coverage of `app/`; CI fails below 90%.
6. **Each phase is a release.** A phase ends with a changelog section and an annotated tag
   (`v0.1.0` for Phase 0 through `v1.0.0`).
7. **Dependabot** opens grouped update PRs monthly for Python dependencies and GitHub Actions.
8. **"Require branches to be up to date before merging" is off.** With one maintainer, PRs merge one
   at a time from a recent `main`, so the extra CI run adds delay without catching anything.

## Alternatives considered
- **Pushing to `main` directly (trunk-based, no PRs):** less ceremony, but nothing stops a failing
  commit from landing, and there is no review record per slice.
- **Squash merges:** a linear `main` with one commit per PR, at the cost of the step-level history
  that the build record relies on.
- **Required approving reviews:** standard on a team; cannot be satisfied by a single maintainer.
- **pre-commit hooks:** catch formatting before a commit is created. Deferred: `make check` and the
  CI gate already enforce the same rules, and a hook framework is one more tool to maintain.
- **`just`, `poe` or shell scripts instead of Make:** friendlier syntax in places, but Make is
  preinstalled on Linux and macOS and widely recognized.
- **A coverage threshold of 100%:** matches today's figure, but encourages tests written to satisfy
  the number once process entry points and signal handlers exist.

## Consequences
- A broken `main` requires deliberately disabling the rule; routine mistakes are caught by CI.
- Every change costs a branch and a PR, even a one-line fix.
- The required check is identified by the CI job name `backend`; renaming the job requires updating the rule.
- If collaborators join, required approvals and the up-to-date requirement (or a merge queue) should be turned on.
- Line coverage does not prove behaviour is tested; it only shows what was never executed.
  Failure-injection tests remain a separate requirement for durability features.
