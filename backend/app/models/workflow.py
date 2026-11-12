import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class RunStatus(enum.StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(enum.StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    RETRYING = "retrying"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    COMPLETED = "completed"
    FAILED = "failed"


def _status_column_type(enum_cls: type[enum.StrEnum], name: str) -> Enum:
    # VARCHAR + CHECK constraint rather than a native PostgreSQL ENUM type: adding or removing
    # a state is then an ordinary constraint change in a migration (ADR-0003).
    return Enum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=32,
        values_callable=lambda members: [member.value for member in members],
    )


# Columns with defaults set both `default` (applied by the ORM) and `server_default` (applied by
# PostgreSQL), so rows inserted with plain SQL, as worker queries may do, are still valid.


class WorkflowTemplate(TimestampMixin, Base):
    """A reusable workflow definition. Its task graph is stored as one validated JSONB document."""

    __tablename__ = "workflow_templates"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    description: Mapped[str] = mapped_column(Text, default="", server_default="")
    definition: Mapped[dict[str, Any]] = mapped_column(JSONB)


class WorkflowRun(TimestampMixin, Base):
    """One execution of a template."""

    __tablename__ = "workflow_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # RESTRICT: a template with execution history cannot be deleted out from under it.
    template_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflow_templates.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[RunStatus] = mapped_column(
        _status_column_type(RunStatus, "run_status"),
        default=RunStatus.PENDING,
        server_default=RunStatus.PENDING.value,
        index=True,
    )
    input: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Task(TimestampMixin, Base):
    """One step of a run. Its own row, because workers lock and update tasks individually."""

    __tablename__ = "tasks"
    __table_args__ = (
        UniqueConstraint("run_id", "key"),
        UniqueConstraint("run_id", "position"),
        # `id` is already unique on its own. This constraint exists so that task_dependencies
        # can reference the pair (run_id, id), which a foreign key may only do if the pair is
        # declared unique.
        UniqueConstraint("run_id", "id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # CASCADE: tasks have no meaning without their run.
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workflow_runs.id", ondelete="CASCADE"))
    key: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(200))
    # Index of the task in the template definition. All tasks of a run are inserted in one
    # transaction and share one created_at, so this is the only stable ordering they have.
    position: Mapped[int]
    status: Mapped[TaskStatus] = mapped_column(
        _status_column_type(TaskStatus, "task_status"),
        default=TaskStatus.PENDING,
        server_default=TaskStatus.PENDING.value,
        index=True,
    )
    input: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    output: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text)
    attempt_count: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TaskDependency(Base):
    """An edge of a run's task graph: `task_id` may not start until `depends_on_task_id` completes.

    Rows are written once, when the run is created, and never updated.
    """

    __tablename__ = "task_dependencies"
    __table_args__ = (
        # Both foreign keys include run_id, and a row has only one run_id, so both ends of an
        # edge are forced to belong to the same run. Two single-column keys to tasks.id would
        # allow an edge between tasks of different runs.
        ForeignKeyConstraint(
            ["run_id", "task_id"],
            ["tasks.run_id", "tasks.id"],
            name="fk_task_dependencies_task_id_tasks",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["run_id", "depends_on_task_id"],
            ["tasks.run_id", "tasks.id"],
            name="fk_task_dependencies_depends_on_task_id_tasks",
            ondelete="CASCADE",
        ),
        CheckConstraint("task_id <> depends_on_task_id", name="no_self_dependency"),
    )

    run_id: Mapped[uuid.UUID]
    # The primary key (task_id, depends_on_task_id) stores each edge at most once and serves
    # "what does this task wait for". The separate index on depends_on_task_id serves the
    # opposite question, "which tasks wait for this one", asked whenever a task completes.
    task_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    depends_on_task_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, index=True)
