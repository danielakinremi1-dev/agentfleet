"""Task dependencies and task position.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-11

Adds what run creation needs to store a task graph (design doc 0001, ADR-0009):

- `tasks.position`: the task's index in the template definition, unique within a run.
- A unique constraint on `tasks (run_id, id)`, so composite foreign keys can reference it.
- `task_dependencies`: one row per edge. Both ends reference `tasks (run_id, id)` through a
  shared `run_id` column, so an edge cannot connect tasks of different runs.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # A NOT NULL column cannot be added to a table that already has rows unless every row gets
    # a value. So: add it nullable, fill it in, then tighten it. Existing tasks are numbered
    # within their run in a deterministic order.
    op.add_column("tasks", sa.Column("position", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE tasks
        SET position = numbered.position
        FROM (
            SELECT id, row_number() OVER (PARTITION BY run_id ORDER BY created_at, key) - 1
                AS position
            FROM tasks
        ) AS numbered
        WHERE tasks.id = numbered.id
        """
    )
    op.alter_column("tasks", "position", nullable=False)
    op.create_unique_constraint(op.f("uq_tasks_run_id_position"), "tasks", ["run_id", "position"])
    op.create_unique_constraint(op.f("uq_tasks_run_id_id"), "tasks", ["run_id", "id"])

    op.create_table(
        "task_dependencies",
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("depends_on_task_id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("task_id", "depends_on_task_id", name=op.f("pk_task_dependencies")),
        sa.ForeignKeyConstraint(
            ["run_id", "task_id"],
            ["tasks.run_id", "tasks.id"],
            name="fk_task_dependencies_task_id_tasks",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["run_id", "depends_on_task_id"],
            ["tasks.run_id", "tasks.id"],
            name="fk_task_dependencies_depends_on_task_id_tasks",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "task_id <> depends_on_task_id",
            name=op.f("ck_task_dependencies_no_self_dependency"),
        ),
    )
    op.create_index(
        op.f("ix_task_dependencies_depends_on_task_id"),
        "task_dependencies",
        ["depends_on_task_id"],
    )


def downgrade() -> None:
    op.drop_table("task_dependencies")
    op.drop_constraint(op.f("uq_tasks_run_id_id"), "tasks", type_="unique")
    op.drop_constraint(op.f("uq_tasks_run_id_position"), "tasks", type_="unique")
    op.drop_column("tasks", "position")
