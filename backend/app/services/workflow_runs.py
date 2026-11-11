"""Workflow run use cases. Framework-agnostic: callable from the API, workers or scripts."""

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RunStatus, Task, TaskDependency, TaskStatus, WorkflowRun
from app.schemas.run import RunCreate
from app.schemas.workflow import WorkflowDefinition
from app.services import workflow_templates


class TemplateNotFoundError(Exception):
    def __init__(self, template_id: uuid.UUID) -> None:
        super().__init__(f"workflow template {template_id} not found")
        self.template_id = template_id


class InvalidTemplateDefinitionError(Exception):
    """The stored definition of a template does not describe a runnable task graph."""

    def __init__(self, template_id: uuid.UUID, reasons: Sequence[str]) -> None:
        super().__init__(
            f"workflow template {template_id} has an invalid definition: {'; '.join(reasons)}"
        )
        self.template_id = template_id
        self.reasons = list(reasons)


@dataclass(frozen=True)
class RunDetail:
    """A run with its task graph."""

    run: WorkflowRun
    # In definition order.
    tasks: Sequence[Task]
    # Task ID to the keys of the tasks it waits for.
    depends_on: Mapping[uuid.UUID, Sequence[str]]


def materialize(
    template_id: uuid.UUID, definition: WorkflowDefinition, run_input: dict[str, Any]
) -> tuple[WorkflowRun, list[Task], list[TaskDependency]]:
    """Build the rows of a new run from a validated definition. Touches no database.

    IDs are generated here rather than by the database, so the dependency rows can refer to
    task rows that have not been inserted yet.
    """
    run = WorkflowRun(
        id=uuid.uuid4(), template_id=template_id, status=RunStatus.PENDING, input=run_input
    )
    task_ids = {task.key: uuid.uuid4() for task in definition.tasks}
    tasks = [
        Task(
            id=task_ids[task.key],
            run_id=run.id,
            key=task.key,
            name=task.name,
            position=position,
            # Nothing is queued at creation. Deciding which tasks are ready belongs to the
            # scheduler, so that rule exists in one place.
            status=TaskStatus.PENDING,
        )
        for position, task in enumerate(definition.tasks)
    ]
    dependencies = [
        TaskDependency(
            run_id=run.id, task_id=task_ids[task.key], depends_on_task_id=task_ids[dependency]
        )
        for task in definition.tasks
        for dependency in task.depends_on
    ]
    return run, tasks, dependencies


async def create_run(session: AsyncSession, template_id: uuid.UUID, data: RunCreate) -> RunDetail:
    template = await workflow_templates.get_template(session, template_id, block_delete=True)
    if template is None:
        raise TemplateNotFoundError(template_id)

    # The definition is validated again although it was validated when the template was saved.
    # It is JSON in the database, which cannot enforce "no cycles": it may predate a validation
    # rule or have been edited by hand. Tasks are only ever created from a graph known to be valid.
    try:
        definition = WorkflowDefinition.model_validate(template.definition)
    except ValidationError as exc:
        reasons = [error["msg"] for error in exc.errors()]
        raise InvalidTemplateDefinitionError(template_id, reasons) from exc

    run, tasks, dependencies = materialize(template.id, definition, data.input)

    # flush() sends the INSERTs inside the open transaction without committing. Parents go
    # first so that every foreign key finds its target. If any step fails, or the process dies,
    # the transaction never commits and none of the rows exist.
    session.add(run)
    await session.flush()
    session.add_all(tasks)
    await session.flush()
    session.add_all(dependencies)
    # Commit before returning, so callers never report a run that is not yet durable.
    await session.commit()
    return _assemble(run, tasks, dependencies)


async def get_run(session: AsyncSession, run_id: uuid.UUID) -> RunDetail | None:
    run = await session.get(WorkflowRun, run_id)
    if run is None:
        return None
    tasks = (
        await session.scalars(select(Task).where(Task.run_id == run_id).order_by(Task.position))
    ).all()
    # Looked up by task ID, the leading column of the table's primary key, so this is an index
    # lookup per task. The table has no index on run_id alone.
    dependencies = (
        await session.scalars(
            select(TaskDependency).where(TaskDependency.task_id.in_([task.id for task in tasks]))
        )
    ).all()
    return _assemble(run, tasks, dependencies)


async def list_runs(session: AsyncSession, *, limit: int, offset: int) -> Sequence[WorkflowRun]:
    statement = (
        select(WorkflowRun)
        # id as a tie-breaker keeps pagination stable when timestamps are equal.
        .order_by(WorkflowRun.created_at.desc(), WorkflowRun.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return (await session.scalars(statement)).all()


def _assemble(
    run: WorkflowRun, tasks: Sequence[Task], dependencies: Sequence[TaskDependency]
) -> RunDetail:
    """Express each task's dependencies as task keys, ordered by the dependency's position.

    Used after both creating and reading a run, so both return the graph in the same form.
    """
    by_id = {task.id: task for task in tasks}
    waits_for: dict[uuid.UUID, list[Task]] = {task.id: [] for task in tasks}
    for edge in dependencies:
        waits_for[edge.task_id].append(by_id[edge.depends_on_task_id])
    depends_on = {
        task_id: [task.key for task in sorted(needed, key=lambda task: task.position)]
        for task_id, needed in waits_for.items()
    }
    return RunDetail(run=run, tasks=tasks, depends_on=depends_on)
