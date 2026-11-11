"""Run creation at the service level: what is written, and what is left behind on failure."""

import uuid
from typing import Any

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.models import RunStatus, Task, TaskDependency, TaskStatus, WorkflowRun, WorkflowTemplate
from app.schemas.run import RunCreate
from app.services import workflow_runs, workflow_templates
from app.services.workflow_runs import InvalidTemplateDefinitionError, TemplateNotFoundError
from tests.sql_hooks import InjectedFailure, watch_statements

DIAMOND: dict[str, Any] = {
    "tasks": [
        {"key": "gather", "name": "Gather evidence", "depends_on": []},
        {"key": "logs", "name": "Analyze logs", "depends_on": ["gather"]},
        {"key": "deploys", "name": "Check deployments", "depends_on": ["gather"]},
        # Listed against definition order on purpose: the stored graph has no edge order, so
        # results use the order of the tasks themselves.
        {"key": "report", "name": "Write report", "depends_on": ["deploys", "logs"]},
    ]
}
CYCLIC: dict[str, Any] = {
    "tasks": [
        {"key": "a", "name": "A", "depends_on": ["b"]},
        {"key": "b", "name": "B", "depends_on": ["a"]},
    ]
}


async def save_template(
    sessionmaker: async_sessionmaker[AsyncSession], definition: dict[str, Any], name: str = "t"
) -> uuid.UUID:
    # Written with the ORM, not the API, so a test can also store a definition the API refuses.
    async with sessionmaker() as session:
        template = WorkflowTemplate(name=name, definition=definition)
        session.add(template)
        await session.commit()
        return template.id


async def count_rows(sessionmaker: async_sessionmaker[AsyncSession]) -> dict[str, int]:
    # A new session, so the counts are what is committed, not what one session has pending.
    async with sessionmaker() as session:
        return {
            model.__tablename__: await session.scalar(select(func.count()).select_from(model)) or 0
            for model in (WorkflowRun, Task, TaskDependency)
        }


NOTHING = {"workflow_runs": 0, "tasks": 0, "task_dependencies": 0}


async def test_create_run_stores_the_graph_of_the_definition(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    template_id = await save_template(sessionmaker, DIAMOND)

    async with sessionmaker() as session:
        created = await workflow_runs.create_run(
            session, template_id, RunCreate(input={"incident": "latency spike"})
        )

    async with sessionmaker() as session:
        run = await session.get(WorkflowRun, created.run.id)
        assert run is not None
        assert (run.template_id, run.status, run.input) == (
            template_id,
            RunStatus.PENDING,
            {"incident": "latency spike"},
        )
        assert run.started_at is None

        tasks = (await session.scalars(select(Task).order_by(Task.position))).all()
        assert [(task.key, task.name) for task in tasks] == [
            ("gather", "Gather evidence"),
            ("logs", "Analyze logs"),
            ("deploys", "Check deployments"),
            ("report", "Write report"),
        ]
        assert all(task.run_id == run.id and task.status is TaskStatus.PENDING for task in tasks)

        key_of = {task.id: task.key for task in tasks}
        edges = (await session.scalars(select(TaskDependency))).all()
        assert all(edge.run_id == run.id for edge in edges)
        assert sorted(
            (key_of[edge.task_id], key_of[edge.depends_on_task_id]) for edge in edges
        ) == [
            ("deploys", "gather"),
            ("logs", "gather"),
            ("report", "deploys"),
            ("report", "logs"),
        ]


async def test_get_run_returns_the_same_graph_create_run_returned(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    template_id = await save_template(sessionmaker, DIAMOND)
    async with sessionmaker() as session:
        created = await workflow_runs.create_run(session, template_id, RunCreate())
    async with sessionmaker() as session:
        fetched = await workflow_runs.get_run(session, created.run.id)

    assert fetched is not None
    assert [task.id for task in fetched.tasks] == [task.id for task in created.tasks]
    assert fetched.depends_on == created.depends_on
    by_key = {task.key: fetched.depends_on[task.id] for task in fetched.tasks}
    assert by_key == {
        "gather": [],
        "logs": ["gather"],
        "deploys": ["gather"],
        "report": ["logs", "deploys"],
    }


async def test_get_run_returns_none_for_an_unknown_id(session: AsyncSession) -> None:
    assert await workflow_runs.get_run(session, uuid.uuid4()) is None


async def test_two_runs_of_one_template_share_no_rows(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    template_id = await save_template(sessionmaker, DIAMOND)
    async with sessionmaker() as session:
        first = await workflow_runs.create_run(session, template_id, RunCreate())
    async with sessionmaker() as session:
        second = await workflow_runs.create_run(session, template_id, RunCreate())

    assert first.run.id != second.run.id
    assert {task.id for task in first.tasks}.isdisjoint(task.id for task in second.tasks)
    assert await count_rows(sessionmaker) == {
        "workflow_runs": 2,
        "tasks": 8,
        "task_dependencies": 8,
    }


async def test_unknown_template_creates_nothing(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    async with sessionmaker() as session:
        with pytest.raises(TemplateNotFoundError):
            await workflow_runs.create_run(session, uuid.uuid4(), RunCreate())
    assert await count_rows(sessionmaker) == NOTHING


async def test_invalid_stored_definition_is_refused_and_creates_nothing(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    template_id = await save_template(sessionmaker, CYCLIC)

    async with sessionmaker() as session:
        with pytest.raises(InvalidTemplateDefinitionError, match="dependency cycle: a -> b -> a"):
            await workflow_runs.create_run(session, template_id, RunCreate())
    assert await count_rows(sessionmaker) == NOTHING


@pytest.mark.parametrize(
    ("failing_statement", "already_sent"),
    [
        ("INSERT INTO tasks", ["INSERT INTO workflow_runs"]),
        ("INSERT INTO task_dependencies", ["INSERT INTO workflow_runs", "INSERT INTO tasks"]),
    ],
    ids=["while inserting tasks", "while inserting dependencies"],
)
async def test_failure_part_way_through_creation_leaves_no_rows(
    engine: AsyncEngine,
    sessionmaker: async_sessionmaker[AsyncSession],
    failing_statement: str,
    already_sent: list[str],
) -> None:
    template_id = await save_template(sessionmaker, DIAMOND)

    async with sessionmaker() as session:
        with (
            watch_statements(engine, fail_on=failing_statement) as sent,
            pytest.raises(InjectedFailure),
        ):
            await workflow_runs.create_run(session, template_id, RunCreate())

    # The earlier inserts really reached the database before the failure...
    inserts = [statement for statement in sent if statement.startswith("INSERT")]
    assert [statement.split(" (")[0] for statement in inserts] == already_sent
    # ...and none of them survived, because the transaction they were part of never committed.
    assert await count_rows(sessionmaker) == NOTHING


async def test_creation_after_a_failed_attempt_succeeds(
    engine: AsyncEngine, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    template_id = await save_template(sessionmaker, DIAMOND)
    async with sessionmaker() as session:
        with (
            watch_statements(engine, fail_on="INSERT INTO task_dependencies"),
            pytest.raises(InjectedFailure),
        ):
            await workflow_runs.create_run(session, template_id, RunCreate())

    async with sessionmaker() as session:
        await workflow_runs.create_run(session, template_id, RunCreate())
    assert await count_rows(sessionmaker) == {
        "workflow_runs": 1,
        "tasks": 4,
        "task_dependencies": 4,
    }


async def test_create_run_reads_the_template_with_a_key_share_lock(
    engine: AsyncEngine, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    template_id = await save_template(sessionmaker, DIAMOND)
    async with sessionmaker() as session:
        with watch_statements(engine) as sent:
            await workflow_runs.create_run(session, template_id, RunCreate())

    template_reads = [statement for statement in sent if "FROM workflow_templates" in statement]
    assert len(template_reads) == 1
    assert template_reads[0].rstrip().endswith("FOR KEY SHARE")


@pytest.mark.parametrize("block_delete", [True, False])
async def test_block_delete_holds_off_a_concurrent_delete(
    sessionmaker: async_sessionmaker[AsyncSession], block_delete: bool
) -> None:
    template_id = await save_template(sessionmaker, DIAMOND)
    delete = text("DELETE FROM workflow_templates WHERE id = :id")

    async with sessionmaker() as reader, sessionmaker() as deleter:
        # The reader's transaction stays open, as it does in create_run until its commit.
        await workflow_templates.get_template(reader, template_id, block_delete=block_delete)
        # Give up waiting for a lock after 200 ms instead of waiting for the reader forever.
        await deleter.execute(text("SET LOCAL lock_timeout = '200ms'"))

        if block_delete:
            with pytest.raises(DBAPIError, match="lock timeout"):
                await deleter.execute(delete, {"id": template_id})
        else:
            # The control case: with a plain read, nothing stands in the way of the delete.
            await deleter.execute(delete, {"id": template_id})
            await deleter.commit()

    async with sessionmaker() as session:
        still_there = await session.get(WorkflowTemplate, template_id)
    assert (still_there is not None) == block_delete


async def test_list_runs_is_newest_first(sessionmaker: async_sessionmaker[AsyncSession]) -> None:
    template_id = await save_template(sessionmaker, DIAMOND)
    created = []
    for _ in range(3):
        async with sessionmaker() as session:
            created.append((await workflow_runs.create_run(session, template_id, RunCreate())).run)

    async with sessionmaker() as session:
        listed = await workflow_runs.list_runs(session, limit=2, offset=0)
        rest = await workflow_runs.list_runs(session, limit=2, offset=2)

    assert [run.id for run in listed] == [created[2].id, created[1].id]
    assert [run.id for run in rest] == [created[0].id]
