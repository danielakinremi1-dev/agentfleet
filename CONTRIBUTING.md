# Contributing and delivery workflow

How changes move from an idea to `main`. The reasoning behind these rules is recorded in
[ADR-0006](docs/decisions/0006-delivery-workflow.md).

## The short version
1. Pick the next unchecked slice in [`docs/roadmap.md`](docs/roadmap.md).
2. Create a branch: `slice/<n>-<short-name>`.
3. Work in small commits, one logical step each, using Conventional Commits.
4. Run `make check` before pushing.
5. Open a pull request. CI must pass before it can be merged.
6. The maintainer reviews and merges. Nobody pushes to `main` directly.

## Units of work
| Unit | Size | Ends with |
|---|---|---|
| **Phase** | A capability of the system (for example "durable execution") | An end-of-phase review, a changelog entry and a release tag |
| **Slice** | About 2-4 hours of work | One pull request and one slice note in `docs/slices/` |
| **Step** | One checkbox in the roadmap | One commit |

Core subsystems start with a design doc ([`docs/design-docs/`](docs/design-docs/)) before code is written.

## Local setup
Requirements: Docker, [uv](https://docs.astral.sh/uv/) and GNU Make.

```bash
make setup    # create .env, install locked dependencies
make up       # start PostgreSQL
make run      # apply migrations and start the API with auto-reload
make check    # everything CI runs
```

`make help` lists every command.

## Commits
[Conventional Commits](https://www.conventionalcommits.org/): `<type>: <summary in the imperative>`.

| Type | Use for |
|---|---|
| `feat` | New behaviour |
| `fix` | A bug fix |
| `test` | Tests only |
| `docs` | Documentation only |
| `refactor` | Restructuring with no behaviour change |
| `build` | Dependencies, packaging, Makefile |
| `ci` | The CI pipeline |

The body explains why the change was made when the summary is not enough. Each commit should
leave the checks passing, so any commit can be checked out and run.

## Pull requests
- One slice per pull request. Refactors that are not needed by the slice go in their own PR.
- The description follows the [template](.github/pull_request_template.md): summary, how to verify,
  checklist and open questions (the default chosen and the alternative).
- PRs are merged with a merge commit, which keeps the step-by-step commits and marks where each
  slice landed.

## Checks on every pull request
The `backend` CI job must pass before a PR can be merged. Each step is a Makefile target.

| Step | Target | What it catches |
|---|---|---|
| Install | `make install` | A lockfile that no longer matches `pyproject.toml` |
| Lint | `make lint` | Likely bugs, unused code, outdated syntax |
| Format | `make format-check` | Unformatted files |
| Types | `make typecheck` | Type errors (mypy strict) |
| Migrations | `make migrate` | A migration that fails on an empty database |
| Drift | `make migration-check` | A model changed without a migration |
| Tests | `make coverage` | Failing tests, or branch coverage of `app/` below 90% |

## Branch protection on `main`
- Changes reach `main` only through a pull request; this applies to administrators too.
- The `backend` status check is required.
- Force pushes and deletion of `main` are blocked.
- Required approvals are set to zero because the project has one maintainer and GitHub does not
  allow approving your own pull request. The CI gate still applies.

The rule requires the check named `backend`. If that CI job is renamed, update the rule.

## Releases
Each completed phase is a release: Phase 0 is `v0.1.0`, Phase 1 is `v0.2.0`, and so on to `v1.0.0`
for the finished project.

1. The last PR of the phase fills in the end-of-phase review in the roadmap and moves the
   `Unreleased` entries in [`CHANGELOG.md`](CHANGELOG.md) under the new version.
2. After it is merged, the merge commit is tagged (`git tag -a v0.2.0`) and published as a GitHub release.

## Documentation with every change
| Change | Document |
|---|---|
| A slice is finished | Slice note in `docs/slices/` |
| An architectural decision is made | ADR in `docs/decisions/` |
| A core subsystem is about to be built | Design doc in `docs/design-docs/` |
| A tool or library is introduced | Entry in `docs/technology-guide.md` |
| A phase is finished | Architecture overview in `docs/architecture/` and the end-of-phase review in the roadmap |
| Anything user-visible changes | `CHANGELOG.md` |
| A step, slice or phase is completed | Checkbox and Progress table in `docs/roadmap.md` |

## Never commit
Secrets, credentials, `.env`, personal information, or anything under `notes/`.
