# AgentFleet developer commands. Run `make help` for the list.
#
# CI calls these same targets (.github/workflows/ci.yml), so `make check` passing locally
# means the pipeline will pass: there is one definition of each check, not two.

.DEFAULT_GOAL := help
.PHONY: help setup install up down migrate migration migration-check run \
        lint format format-check typecheck test coverage check

BACKEND := backend
UV_RUN  := cd $(BACKEND) && uv run

help: ## List available commands
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# --- Setup -------------------------------------------------------------------

setup: install ## First-time setup: create .env and install dependencies
	@test -f .env || (cp .env.example .env && echo "Created .env from .env.example")

install: ## Install dependencies exactly as pinned in uv.lock
	cd $(BACKEND) && uv sync --locked

# --- Local services ----------------------------------------------------------

up: ## Start PostgreSQL and wait until it accepts connections
	docker compose up -d --wait db

down: ## Stop containers (database data is kept in its volume)
	docker compose down

# --- Database ----------------------------------------------------------------

migrate: ## Apply all pending migrations
	$(UV_RUN) alembic upgrade head

# Revision IDs are sequential (0001, 0002, ...) so the order of migrations is readable
# in a directory listing; the next ID is the number of existing revisions plus one.
migration: ## Draft a migration from model changes: make migration m="add users table"
	@test -n "$(m)" || (echo 'Usage: make migration m="describe the change"' && exit 1)
	$(UV_RUN) alembic revision --autogenerate -m "$(m)" \
		--rev-id $$(printf '%04d' $$(( $$(ls migrations/versions/*.py | wc -l) + 1 )))
	@echo "Review the generated file by hand before committing (renames and CHECK constraints are not detected)."

migration-check: ## Fail if the models and the migrations have drifted apart
	$(UV_RUN) alembic check

# --- Run ---------------------------------------------------------------------

run: migrate ## Run the API with auto-reload (http://localhost:8000/docs)
	$(UV_RUN) uvicorn app.main:app --reload

# --- Quality checks ----------------------------------------------------------

lint: ## Lint with ruff
	$(UV_RUN) ruff check .

format: ## Format code and apply safe lint fixes
	$(UV_RUN) ruff format . && uv run ruff check --fix .

format-check: ## Fail if any file is not formatted
	$(UV_RUN) ruff format --check .

typecheck: ## Type-check with mypy (strict)
	$(UV_RUN) mypy

test: ## Run tests; pass pytest options with args, e.g. make test args="-k health -x"
	$(UV_RUN) pytest $(args)

coverage: ## Run tests and fail if coverage is below the threshold in pyproject.toml
	$(UV_RUN) pytest --cov --cov-report=term-missing

check: lint format-check typecheck migrate migration-check coverage ## Run everything CI runs
