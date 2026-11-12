"""Database-level guarantees: constraints hold even if application code has a bug."""

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import RunStatus, Task, TaskDependency, TaskStatus, WorkflowRun, WorkflowTemplate


async def make_run(session: AsyncSession, name: str = "t") -> WorkflowRun:
    template = WorkflowTemplate(name=name, definition={"tasks": []})
    session.add(template)
    await session.flush()  # Sends the INSERT so template.id exists in the database.
    run = WorkflowRun(template_id=template.id, input={"incident": "latency spike"})
    session.add(run)
    await session.flush()
    return run


async def make_tasks(session: AsyncSession, run: WorkflowRun, *keys: str) -> list[Task]:
    tasks = [
        Task(run_id=run.id, key=key, name=key, position=position)
        for position, key in enumerate(keys)
    ]
    session.add_all(tasks)
    await session.flush()
    return tasks


async def test_run_and_tasks_get_defaults(session: AsyncSession) -> None:
    run = await make_run(session)
    session.add(Task(run_id=run.id, key="gather_evidence", name="Gather evidence", position=0))
    await session.commit()

    task = await session.scalar(select(Task).where(Task.run_id == run.id))
    assert task is not None
    assert run.status is RunStatus.PENDING
    assert task.status is TaskStatus.PENDING
    assert task.attempt_count == 0
    assert task.created_at is not None


async def test_database_rejects_unknown_status(session: AsyncSession) -> None:
    run = await make_run(session)
    await session.commit()
    # Raw SQL bypasses the Python enum, so only the CHECK constraint stands in the way.
    with pytest.raises(IntegrityError, match="ck_workflow_runs_run_status"):
        await session.execute(
            text("UPDATE workflow_runs SET status = 'compelted' WHERE id = :id"), {"id": run.id}
        )


async def test_task_keys_are_unique_within_a_run(session: AsyncSession) -> None:
    run = await make_run(session)
    session.add_all(
        [
            Task(run_id=run.id, key="same", name="A", position=0),
            Task(run_id=run.id, key="same", name="B", position=1),
        ]
    )
    with pytest.raises(IntegrityError, match="uq_tasks_run_id_key"):
        await session.commit()


async def test_task_positions_are_unique_within_a_run(session: AsyncSession) -> None:
    run = await make_run(session)
    session.add_all(
        [
            Task(run_id=run.id, key="a", name="A", position=0),
            Task(run_id=run.id, key="b", name="B", position=0),
        ]
    )
    with pytest.raises(IntegrityError, match="uq_tasks_run_id_position"):
        await session.commit()


async def test_deleting_a_run_deletes_its_tasks(session: AsyncSession) -> None:
    run = await make_run(session)
    first, second = await make_tasks(session, run, "a", "b")
    session.add(TaskDependency(run_id=run.id, task_id=second.id, depends_on_task_id=first.id))
    await session.commit()

    await session.execute(text("DELETE FROM workflow_runs WHERE id = :id"), {"id": run.id})
    await session.commit()
    # The delete cascades from the run to its tasks, and from the tasks to their edges.
    assert await session.scalar(select(func.count()).select_from(Task)) == 0
    assert await session.scalar(select(func.count()).select_from(TaskDependency)) == 0


async def test_template_with_runs_cannot_be_deleted(session: AsyncSession) -> None:
    run = await make_run(session)
    await session.commit()
    with pytest.raises(IntegrityError, match="fk_workflow_runs_template_id_workflow_templates"):
        await session.execute(
            text("DELETE FROM workflow_templates WHERE id = :id"), {"id": run.template_id}
        )


async def test_failed_commit_persists_nothing(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    # One unit of work: a template, a run and two tasks, one of which violates a constraint.
    async with sessionmaker() as session:
        run = await make_run(session, name="atomic")
        session.add_all(
            [
                Task(run_id=run.id, key="x", name="X", position=0),
                Task(run_id=run.id, key="x", name="Y", position=1),
            ]
        )
        with pytest.raises(IntegrityError):
            await session.commit()

    # Nothing from that transaction survives, including the rows that were valid on their own.
    async with sessionmaker() as session:
        for model in (WorkflowTemplate, WorkflowRun, Task):
            assert await session.scalar(select(func.count()).select_from(model)) == 0


async def test_dependency_cannot_connect_tasks_of_different_runs(session: AsyncSession) -> None:
    first_run = await make_run(session, name="first")
    second_run = await make_run(session, name="second")
    (mine,) = await make_tasks(session, first_run, "a")
    (theirs,) = await make_tasks(session, second_run, "a")

    # Both tasks exist, so a foreign key to tasks.id alone would accept this edge. The composite
    # key looks for (first_run.id, theirs.id), and no task has that pair.
    session.add(TaskDependency(run_id=first_run.id, task_id=mine.id, depends_on_task_id=theirs.id))
    with pytest.raises(IntegrityError, match="fk_task_dependencies_depends_on_task_id_tasks"):
        await session.commit()


async def test_dependency_run_must_match_its_tasks(session: AsyncSession) -> None:
    first_run = await make_run(session, name="first")
    second_run = await make_run(session, name="second")
    a, b = await make_tasks(session, first_run, "a", "b")

    # Both ends are in the first run, but the edge claims to belong to the second.
    session.add(TaskDependency(run_id=second_run.id, task_id=b.id, depends_on_task_id=a.id))
    with pytest.raises(IntegrityError, match="fk_task_dependencies_"):
        await session.commit()


async def test_task_cannot_depend_on_itself(session: AsyncSession) -> None:
    run = await make_run(session)
    (task,) = await make_tasks(session, run, "a")
    session.add(TaskDependency(run_id=run.id, task_id=task.id, depends_on_task_id=task.id))
    with pytest.raises(IntegrityError, match="ck_task_dependencies_no_self_dependency"):
        await session.commit()


async def test_dependency_is_stored_at_most_once(session: AsyncSession) -> None:
    run = await make_run(session)
    a, b = await make_tasks(session, run, "a", "b")
    await session.commit()

    edge = {"run_id": run.id, "task_id": b.id, "depends_on_task_id": a.id}
    statement = text(
        "INSERT INTO task_dependencies (run_id, task_id, depends_on_task_id) "
        "VALUES (:run_id, :task_id, :depends_on_task_id)"
    )
    await session.execute(statement, edge)
    with pytest.raises(IntegrityError, match="pk_task_dependencies"):
        await session.execute(statement, edge)
