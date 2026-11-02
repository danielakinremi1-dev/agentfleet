"""Initial schema: workflow templates, runs and tasks.

Revision ID: 0001
Revises:
Create Date: 2026-11-02

Status columns are VARCHAR with explicit CHECK constraints rather than native ENUM types,
so adding a state later is a constraint change (ADR-0003).
"""

from collections.abc import Sequence
from datetime import datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RUN_STATUSES = ("pending", "running", "waiting_for_approval", "completed", "failed", "cancelled")
TASK_STATUSES = (
    "pending",
    "queued",
    "running",
    "retrying",
    "waiting_for_approval",
    "completed",
    "failed",
)


def _in(column: str, values: Sequence[str]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


def _timestamps() -> list[sa.Column[datetime]]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "workflow_templates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("definition", postgresql.JSONB(), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_workflow_templates")),
        sa.UniqueConstraint("name", name=op.f("uq_workflow_templates_name")),
    )

    op.create_table(
        "workflow_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("template_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column(
            "input", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_workflow_runs")),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["workflow_templates.id"],
            name=op.f("fk_workflow_runs_template_id_workflow_templates"),
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(_in("status", RUN_STATUSES), name=op.f("ck_workflow_runs_run_status")),
    )
    op.create_index(op.f("ix_workflow_runs_status"), "workflow_runs", ["status"])
    op.create_index(op.f("ix_workflow_runs_template_id"), "workflow_runs", ["template_id"])

    op.create_table(
        "tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column(
            "input", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column("output", postgresql.JSONB(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tasks")),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["workflow_runs.id"],
            name=op.f("fk_tasks_run_id_workflow_runs"),
            ondelete="CASCADE",
        ),
        # Also serves as the index for "all tasks of a run" (run_id is its leading column).
        sa.UniqueConstraint("run_id", "key", name=op.f("uq_tasks_run_id_key")),
        sa.CheckConstraint(_in("status", TASK_STATUSES), name=op.f("ck_tasks_task_status")),
    )
    op.create_index(op.f("ix_tasks_status"), "tasks", ["status"])


def downgrade() -> None:
    # Reverse dependency order: tasks reference runs, runs reference templates.
    op.drop_table("tasks")
    op.drop_table("workflow_runs")
    op.drop_table("workflow_templates")
