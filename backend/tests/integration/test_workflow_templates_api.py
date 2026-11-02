import asyncio
import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import WorkflowTemplate


def template_payload(name: str = "Incident Investigation") -> dict[str, Any]:
    return {
        "name": name,
        "description": "Investigate an incident and recommend a remediation.",
        "definition": {
            "tasks": [
                {"key": "gather_evidence", "name": "Gather evidence"},
                {"key": "analyze_logs", "name": "Analyze logs", "depends_on": ["gather_evidence"]},
            ]
        },
    }


async def test_create_then_read_template(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    created = await client.post("/api/workflows", json=template_payload())
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "Incident Investigation"
    assert body["definition"]["tasks"][1]["depends_on"] == ["gather_evidence"]

    fetched = await client.get(f"/api/workflows/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == body

    # Read through a separate session: the row was committed, not just echoed back.
    async with sessionmaker() as session:
        stored = await session.get(WorkflowTemplate, uuid.UUID(body["id"]))
    assert stored is not None
    assert stored.definition["tasks"][0]["key"] == "gather_evidence"


async def test_duplicate_name_is_a_conflict(client: AsyncClient) -> None:
    first = await client.post("/api/workflows", json=template_payload())
    second = await client.post("/api/workflows", json=template_payload())
    assert first.status_code == 201
    assert second.status_code == 409
    assert "already exists" in second.json()["detail"]


async def test_concurrent_duplicate_creates_have_one_winner(client: AsyncClient) -> None:
    # Both requests run at the same time on separate connections. The unique constraint,
    # not application code, decides the winner, so there is no check-then-insert race.
    responses = await asyncio.gather(
        *(client.post("/api/workflows", json=template_payload("Race")) for _ in range(5))
    )
    assert sorted(r.status_code for r in responses) == [201, 409, 409, 409, 409]


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p.pop("name"),
        lambda p: p.update(name="   "),
        lambda p: p["definition"].update(tasks=[]),
        lambda p: p.update(unexpected="field"),
        lambda p: p["definition"]["tasks"][1].update(depends_on=["missing"]),
    ],
    ids=["missing-name", "blank-name", "no-tasks", "extra-field", "unknown-dependency"],
)
async def test_invalid_payload_is_rejected(client: AsyncClient, mutate: Any) -> None:
    payload = template_payload()
    mutate(payload)
    response = await client.post("/api/workflows", json=payload)
    assert response.status_code == 422


async def test_unknown_template_is_404(client: AsyncClient) -> None:
    response = await client.get(f"/api/workflows/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_malformed_id_is_422(client: AsyncClient) -> None:
    response = await client.get("/api/workflows/not-a-uuid")
    assert response.status_code == 422


async def test_list_is_newest_first_and_paginated(client: AsyncClient) -> None:
    for name in ("first", "second", "third"):
        assert (await client.post("/api/workflows", json=template_payload(name))).status_code == 201

    page = await client.get("/api/workflows", params={"limit": 2})
    assert page.status_code == 200
    assert [t["name"] for t in page.json()] == ["third", "second"]

    rest = await client.get("/api/workflows", params={"limit": 2, "offset": 2})
    assert [t["name"] for t in rest.json()] == ["first"]


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
async def test_list_rejects_out_of_range_paging(
    client: AsyncClient, params: dict[str, int]
) -> None:
    response = await client.get("/api/workflows", params=params)
    assert response.status_code == 422
