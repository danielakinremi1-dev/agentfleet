"""Database-level guarantees: constraints hold even if application code has a bug."""

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import RunStatus, Task, TaskStatus, WorkflowRun, WorkflowTemplate


async def make_run(session: AsyncSession, name: str = "t") -> WorkflowRun:
    template = WorkflowTemplate(name=name, definition={"tasks": []})
    session.add(template)
    await session.flush()  # Sends the INSERT so template.id exists in the database.
    run = WorkflowRun(template_id=template.id, input={"incident": "latency spike"})
    session.add(run)
    await session.flush()
    return run


async def test_run_and_tasks_get_defaults(session: AsyncSession) -> None:
    run = await make_run(session)
    session.add(Task(run_id=run.id, key="gather_evidence", name="Gather evidence"))
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
        [Task(run_id=run.id, key="same", name="A"), Task(run_id=run.id, key="same", name="B")]
    )
    with pytest.raises(IntegrityError, match="uq_tasks_run_id_key"):
        await session.commit()


async def test_deleting_a_run_deletes_its_tasks(session: AsyncSession) -> None:
    run = await make_run(session)
    session.add(Task(run_id=run.id, key="a", name="A"))
    await session.commit()

    await session.execute(text("DELETE FROM workflow_runs WHERE id = :id"), {"id": run.id})
    await session.commit()
    assert await session.scalar(select(func.count()).select_from(Task)) == 0


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
            [Task(run_id=run.id, key="x", name="X"), Task(run_id=run.id, key="x", name="Y")]
        )
        with pytest.raises(IntegrityError):
            await session.commit()

    # Nothing from that transaction survives, including the rows that were valid on their own.
    async with sessionmaker() as session:
        for model in (WorkflowTemplate, WorkflowRun, Task):
            assert await session.scalar(select(func.count()).select_from(model)) == 0
