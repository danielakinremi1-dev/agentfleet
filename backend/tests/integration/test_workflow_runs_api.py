import asyncio
import uuid
from typing import Any

from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import Task, TaskDependency, WorkflowRun, WorkflowTemplate
from app.schemas.run import MAX_RUN_INPUT_BYTES

DEFINITION: dict[str, Any] = {
    "tasks": [
        {"key": "gather", "name": "Gather evidence"},
        {"key": "logs", "name": "Analyze logs", "depends_on": ["gather"]},
        {"key": "deploys", "name": "Check deployments", "depends_on": ["gather"]},
        {"key": "report", "name": "Write report", "depends_on": ["logs", "deploys"]},
    ]
}


async def create_template(client: AsyncClient, name: str = "Incident Investigation") -> str:
    response = await client.post("/api/workflows", json={"name": name, "definition": DEFINITION})
    assert response.status_code == 201
    template_id: str = response.json()["id"]
    return template_id


async def test_create_run_then_read_it_back(client: AsyncClient) -> None:
    template_id = await create_template(client)

    created = await client.post(
        f"/api/workflows/{template_id}/runs", json={"input": {"incident": "latency spike"}}
    )
    assert created.status_code == 201
    body = created.json()
    assert created.headers["location"] == f"/api/runs/{body['id']}"
    assert body["template_id"] == template_id
    assert body["status"] == "pending"
    assert body["input"] == {"incident": "latency spike"}
    assert body["started_at"] is None
    assert body["finished_at"] is None
    assert [(task["key"], task["status"], task["depends_on"]) for task in body["tasks"]] == [
        ("gather", "pending", []),
        ("logs", "pending", ["gather"]),
        ("deploys", "pending", ["gather"]),
        ("report", "pending", ["logs", "deploys"]),
    ]
    assert body["tasks"][0]["name"] == "Gather evidence"
    assert body["tasks"][0]["attempt_count"] == 0
    assert body["tasks"][0]["output"] is None

    # Follow the Location header: what was reported at creation is what is stored.
    fetched = await client.get(created.headers["location"])
    assert fetched.status_code == 200
    assert fetched.json() == body


async def test_run_input_defaults_to_an_empty_object(client: AsyncClient) -> None:
    template_id = await create_template(client)
    created = await client.post(f"/api/workflows/{template_id}/runs", json={})
    assert created.status_code == 201
    assert created.json()["input"] == {}


async def test_run_of_unknown_template_is_not_found(client: AsyncClient) -> None:
    response = await client.post(f"/api/workflows/{uuid.uuid4()}/runs", json={})
    assert response.status_code == 404
    assert response.json() == {"detail": "workflow template not found"}


async def test_run_of_malformed_template_id_is_unprocessable(client: AsyncClient) -> None:
    response = await client.post("/api/workflows/not-a-uuid/runs", json={})
    assert response.status_code == 422


async def test_template_with_invalid_stored_definition_is_a_conflict(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    # Stored directly, bypassing the API's validation: the situation of a definition saved
    # before cycle detection existed, or edited by hand.
    async with sessionmaker() as session:
        template = WorkflowTemplate(
            name="legacy",
            definition={
                "tasks": [
                    {"key": "a", "name": "A", "depends_on": ["b"]},
                    {"key": "b", "name": "B", "depends_on": ["a"]},
                ]
            },
        )
        session.add(template)
        await session.commit()

    response = await client.post(f"/api/workflows/{template.id}/runs", json={})
    assert response.status_code == 409
    assert "dependency cycle: a -> b -> a" in response.json()["detail"]

    async with sessionmaker() as session:
        assert await session.scalar(select(func.count()).select_from(WorkflowRun)) == 0
        assert await session.scalar(select(func.count()).select_from(Task)) == 0


async def test_invalid_run_input_is_unprocessable(client: AsyncClient) -> None:
    template_id = await create_template(client)
    url = f"/api/workflows/{template_id}/runs"

    not_an_object = await client.post(url, json={"input": ["a", "b"]})
    too_large = await client.post(url, json={"input": {"k": "a" * MAX_RUN_INPUT_BYTES}})
    unknown_field = await client.post(url, json={"input": {}, "priority": "high"})
    nul_character = await client.post(url, json={"input": {"note": "a\x00b"}})
    # Sent as raw text because NaN is not valid JSON, although Python's parser accepts it.
    not_a_number = await client.post(
        url, content='{"input": {"value": NaN}}', headers={"content-type": "application/json"}
    )

    for response in (not_an_object, too_large, unknown_field, nul_character, not_a_number):
        assert response.status_code == 422, response.text
    assert "the limit is 65536" in too_large.text
    assert "NUL" in nul_character.text
    assert "NaN or Infinity" in not_a_number.text
    # The rejected value is described, not repeated back.
    assert "a" * 100 not in too_large.text
    assert all("input" not in error for error in too_large.json()["detail"])
    assert (await client.get("/api/runs")).json() == []


async def test_unknown_run_is_not_found(client: AsyncClient) -> None:
    response = await client.get(f"/api/runs/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json() == {"detail": "workflow run not found"}


async def test_malformed_run_id_is_unprocessable(client: AsyncClient) -> None:
    assert (await client.get("/api/runs/not-a-uuid")).status_code == 422


async def test_list_runs_newest_first_without_tasks(client: AsyncClient) -> None:
    template_id = await create_template(client)
    ids = []
    for incident in ("first", "second", "third"):
        created = await client.post(
            f"/api/workflows/{template_id}/runs", json={"input": {"incident": incident}}
        )
        ids.append(created.json()["id"])

    listed = await client.get("/api/runs")
    assert listed.status_code == 200
    assert [run["id"] for run in listed.json()] == list(reversed(ids))
    assert "tasks" not in listed.json()[0]

    page = await client.get("/api/runs", params={"limit": 1, "offset": 1})
    assert [run["id"] for run in page.json()] == [ids[1]]


async def test_list_runs_rejects_out_of_range_paging(client: AsyncClient) -> None:
    assert (await client.get("/api/runs", params={"limit": 0})).status_code == 422
    assert (await client.get("/api/runs", params={"limit": 101})).status_code == 422
    assert (await client.get("/api/runs", params={"offset": -1})).status_code == 422


async def test_concurrent_runs_of_one_template_are_all_created(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    # Each creation locks the template row FOR KEY SHARE. That lock is shared, so creations
    # neither block nor fail one another; each gets its own complete graph.
    template_id = await create_template(client)
    responses = await asyncio.gather(
        *(client.post(f"/api/workflows/{template_id}/runs", json={}) for _ in range(8))
    )

    assert [response.status_code for response in responses] == [201] * 8
    assert len({response.json()["id"] for response in responses}) == 8
    async with sessionmaker() as session:
        assert await session.scalar(select(func.count()).select_from(Task)) == 8 * 4
        assert await session.scalar(select(func.count()).select_from(TaskDependency)) == 8 * 4
        tasks_per_run = (
            await session.execute(select(func.count()).select_from(Task).group_by(Task.run_id))
        ).scalars()
        assert set(tasks_per_run) == {4}
